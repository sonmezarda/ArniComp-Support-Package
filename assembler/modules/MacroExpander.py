from __future__ import annotations

import ast
import re
from typing import Dict, List, Optional, TYPE_CHECKING, Tuple


if TYPE_CHECKING:
    from .AssemblyHelper import AssemblyHelper, ParsedLine, ResolvedValue
    from .AssemblyHelper import InstructionEncoder


class MacroExpander:
    """Handle instruction aliases, pseudoinstructions, and macro-sized estimates."""

    def __init__(
        self,
        helper: "AssemblyHelper",
        encoder: "InstructionEncoder",
        jump_aliases: Dict[str, str],
        jump_conditions: Dict[str, str],
    ) -> None:
        self.helper = helper
        self.encoder = encoder
        self.jump_aliases = jump_aliases
        self.jump_conditions = jump_conditions

    def normalize_instruction(self, instruction: str, args: List[str]) -> Tuple[str, List[str]]:
        instruction = instruction.upper()
        args = [arg.strip() for arg in args]

        if instruction in self.jump_aliases:
            instruction = self.jump_aliases[instruction]

        if instruction == "JMP" and len(args) == 1 and self.helper.is_jump_name(args[0]):
            return self.helper.canonical_jump_name(args[0]), []

        if instruction == "CLR":
            if len(args) != 1:
                raise ValueError(f"CLR requires 1 argument, got {len(args)}")
            return "MOV", [args[0], "ZERO"]

        if instruction == "ADD" and len(args) == 1 and self.helper.looks_like_nonzero_immediate(args[0]):
            raise ValueError("ADD does not accept immediate operands; use ADDI instead")

        if instruction == "SUB" and len(args) == 1 and self.helper.looks_like_nonzero_immediate(args[0]):
            raise ValueError("SUB does not accept immediate operands; use SUBI instead")

        return instruction, args

    def parse_temp_register_suffix(self, args: List[str], instruction: str) -> Tuple[List[str], str]:
        if not args:
            raise ValueError(f"{instruction} requires at least 1 argument")

        temp_reg = "RA"
        core_args = list(args)
        if len(core_args) >= 2 and core_args[-1].startswith(":"):
            suffix = core_args[-1][1:].strip().upper()
            if suffix not in {"RA", "RD"}:
                raise ValueError(f"{instruction} temporary register suffix must be :RA or :RD, got {core_args[-1]}")
            temp_reg = suffix
            core_args = core_args[:-1]

        return core_args, temp_reg

    def estimate_load_byte_size(self, byte_value: int) -> int:
        return 1 if 0 <= byte_value <= 31 else 2

    def emit_load_byte(self, dest: str, byte_value: int) -> List[str]:
        if not (0 <= byte_value <= 0xFF):
            raise ValueError(f"Byte load value out of range: {byte_value}")
        if byte_value <= 31:
            return [self.encoder.encode_ldl(dest, byte_value)]
        return [
            self.encoder.encode_ldl(dest, byte_value & 0x1F),
            self.encoder.encode_ldh(dest, (byte_value >> 5) & 0x07),
        ]

    def resolve_address_operand(
        self,
        token: str,
        labels: Dict[str, int],
        constants: Dict[str, int],
        instruction: str,
        allow_unresolved: bool = False,
    ) -> "ResolvedValue":
        stripped = token.strip()
        if (
            not stripped.startswith(
                (
                    self.helper.label_prefix,
                    self.helper.constant_prefix,
                    self.helper.number_prefix,
                )
            )
            and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", stripped)
        ):
            label_name = stripped.upper()
            if label_name in labels:
                from .AssemblyHelper import ResolvedValue

                return ResolvedValue(raw_text=token, value=labels[label_name], kind="label")
            if allow_unresolved:
                from .AssemblyHelper import ResolvedValue

                return ResolvedValue(raw_text=token, value=None, kind="label")

        resolved = self.helper.resolve_value(token, labels, constants, allow_unresolved=allow_unresolved)
        if resolved.sliced:
            raise ValueError(f"{instruction} expects an unsliced address operand, got {token}")
        return resolved

    def parse_call_args(self, args: List[str]) -> Tuple[str, str]:
        core_args, temp_reg = self.parse_temp_register_suffix(args, "CALL")
        if len(core_args) != 1:
            raise ValueError(f"CALL requires 1 target operand, got {len(core_args)}")
        return core_args[0], temp_reg

    def parse_jumpa_args(self, args: List[str]) -> Tuple[str, str]:
        core_args, temp_reg = self.parse_temp_register_suffix(args, "JMPA")
        if len(core_args) != 1:
            raise ValueError(f"JMPA requires 1 target operand, got {len(core_args)}")
        return core_args[0], temp_reg

    def parse_jump_target_args(self, args: List[str], instruction: str) -> Tuple[str, str]:
        core_args, temp_reg = self.parse_temp_register_suffix(args, instruction)
        if len(core_args) != 1:
            raise ValueError(f"{instruction} requires 1 target operand, got {len(core_args)}")
        return core_args[0], temp_reg

    def parse_ret_args(self, args: List[str]) -> str:
        if not args:
            return "LR"
        if len(args) == 1 and args[0].strip().upper() == ":STACK":
            return "STACK"
        raise ValueError("RET supports only 'RET' or 'RET :STACK'")

    def parse_pushi_args(self, args: List[str]) -> Tuple[str, str]:
        core_args, temp_reg = self.parse_temp_register_suffix(args, "PUSHI")
        if len(core_args) != 1:
            raise ValueError(f"PUSHI requires 1 value operand, got {len(core_args)}")
        return core_args[0], temp_reg

    def parse_pushstr_args(self, args: List[str]) -> Tuple[str, List[str], str]:
        core_args, temp_reg = self.parse_temp_register_suffix(args, "PUSHSTR")
        if not core_args:
            raise ValueError("PUSHSTR requires at least 1 string operand")
        string_token = core_args[0]
        trailing_values = core_args[1:]
        return string_token, trailing_values, temp_reg

    def parse_string_literal(self, token: str, instruction: str) -> str:
        token = token.strip()
        if len(token) < 2 or token[0] not in {'"', "'"} or token[-1] != token[0]:
            raise ValueError(f"{instruction} expects a quoted string literal, got {token}")
        try:
            literal = ast.literal_eval(token)
        except (SyntaxError, ValueError) as exc:
            raise ValueError(f"Invalid string literal for {instruction}: {token}") from exc
        if not isinstance(literal, str):
            raise ValueError(f"{instruction} expects a string literal, got {token}")
        return literal

    def estimate_value_load_size(
        self,
        token: str,
        labels: Dict[str, int],
        constants: Dict[str, int],
        instruction: str,
    ) -> int:
        resolved = self.helper.resolve_value(token, labels, constants, allow_unresolved=True)
        if resolved.value is None:
            return 2
        if resolved.sliced and resolved.width != 8:
            raise ValueError(f"{instruction} sliced operands must be exactly 8 bits wide")
        return self.estimate_load_byte_size(resolved.value & 0xFF)

    def estimate_absolute_transfer_size(
        self,
        instruction: str,
        args: List[str],
        labels: Dict[str, int],
        constants: Dict[str, int],
        final_op_size: int,
    ) -> int:
        if instruction == "CALL":
            target_token, _ = self.parse_call_args(args)
        else:
            target_token, _ = self.parse_jumpa_args(args)

        resolved = self.resolve_address_operand(target_token, labels, constants, instruction, allow_unresolved=True)
        if resolved.value is None:
            return 4 + final_op_size

        target_value = resolved.value & 0xFFFF
        low_byte = target_value & 0xFF
        high_byte = (target_value >> 8) & 0xFF
        size = self.estimate_load_byte_size(low_byte) + 1 + final_op_size
        if high_byte == 0:
            size += 1
        else:
            size += self.estimate_load_byte_size(high_byte) + 1
        return size

    def estimate_jump_with_target_size(
        self,
        instruction: str,
        args: List[str],
        labels: Dict[str, int],
        constants: Dict[str, int],
        final_ops: List[str],
    ) -> int:
        target_token, _ = self.parse_jump_target_args(args, instruction)
        resolved = self.resolve_address_operand(target_token, labels, constants, instruction, allow_unresolved=True)
        if resolved.value is None:
            return 4 + len(final_ops)

        target_value = resolved.value & 0xFFFF
        low_byte = target_value & 0xFF
        high_byte = (target_value >> 8) & 0xFF
        size = self.estimate_load_byte_size(low_byte) + 1 + len(final_ops)
        if high_byte == 0:
            size += 1
        else:
            size += self.estimate_load_byte_size(high_byte) + 1
        return size

    def estimate_unsigned_gt_target_size(
        self,
        instruction: str,
        args: List[str],
        current_pc: int,
        labels: Dict[str, int],
        constants: Dict[str, int],
    ) -> int:
        target_token, _ = self.parse_jump_target_args(args, instruction)
        _ = self.resolve_address_operand(target_token, labels, constants, instruction, allow_unresolved=True)

        # skip target points to the instruction after the whole macro
        unresolved_skip_size = 4 + 2 + 4 + 1
        for _ in range(8):
            skip_addr = current_pc + unresolved_skip_size
            skip_low = skip_addr & 0xFF
            skip_high = (skip_addr >> 8) & 0xFF
            skip_load_size = self.estimate_load_byte_size(skip_low) + 1
            skip_load_size += 1 if skip_high == 0 else self.estimate_load_byte_size(skip_high) + 1

            target_resolved = self.resolve_address_operand(target_token, labels, constants, instruction, allow_unresolved=True)
            if target_resolved.value is None:
                target_load_size = 4
            else:
                target_value = target_resolved.value & 0xFFFF
                target_low = target_value & 0xFF
                target_high = (target_value >> 8) & 0xFF
                target_load_size = self.estimate_load_byte_size(target_low) + 1
                target_load_size += 1 if target_high == 0 else self.estimate_load_byte_size(target_high) + 1

            size = skip_load_size + 2 + target_load_size + 1
            if size == unresolved_skip_size:
                return size
            unresolved_skip_size = size

        return unresolved_skip_size

    def emit_absolute_transfer(
        self,
        instruction: str,
        args: List[str],
        labels: Dict[str, int],
        constants: Dict[str, int],
        final_op: str,
    ) -> List[str]:
        if instruction == "CALL":
            target_token, temp_reg = self.parse_call_args(args)
        else:
            target_token, temp_reg = self.parse_jumpa_args(args)

        resolved = self.resolve_address_operand(target_token, labels, constants, instruction)
        if resolved.value is None:
            raise ValueError(f"{instruction} could not resolve operand {target_token}")

        target_value = resolved.value & 0xFFFF
        low_byte = target_value & 0xFF
        high_byte = (target_value >> 8) & 0xFF

        emitted: List[str] = []
        emitted.extend(self.emit_load_byte(temp_reg, low_byte))
        emitted.append(self.encoder.encode_mov("PRL", temp_reg))
        if high_byte == 0:
            emitted.append(self.encoder.encode_mov("PRH", "ZERO"))
        else:
            emitted.extend(self.emit_load_byte(temp_reg, high_byte))
            emitted.append(self.encoder.encode_mov("PRH", temp_reg))
        if final_op == "JAL":
            emitted.append(self.encoder.encode_special("JAL"))
        elif final_op == "JMP":
            emitted.append(self.encoder.encode_jump("JMP"))
        else:
            raise ValueError(f"Unsupported absolute transfer final op: {final_op}")
        return emitted

    def emit_jump_with_target(
        self,
        instruction: str,
        args: List[str],
        labels: Dict[str, int],
        constants: Dict[str, int],
        final_ops: List[str],
    ) -> List[str]:
        target_token, temp_reg = self.parse_jump_target_args(args, instruction)
        resolved = self.resolve_address_operand(target_token, labels, constants, instruction)
        if resolved.value is None:
            raise ValueError(f"{instruction} could not resolve operand {target_token}")

        target_value = resolved.value & 0xFFFF
        low_byte = target_value & 0xFF
        high_byte = (target_value >> 8) & 0xFF

        emitted: List[str] = []
        emitted.extend(self.emit_load_byte(temp_reg, low_byte))
        emitted.append(self.encoder.encode_mov("PRL", temp_reg))
        if high_byte == 0:
            emitted.append(self.encoder.encode_mov("PRH", "ZERO"))
        else:
            emitted.extend(self.emit_load_byte(temp_reg, high_byte))
            emitted.append(self.encoder.encode_mov("PRH", temp_reg))

        for op in final_ops:
            if op == "JGT":
                emitted.append(self.encoder.encode_special("JGT"))
            else:
                emitted.append(self.encoder.encode_jump(op))
        return emitted

    def emit_unsigned_gt_target(
        self,
        instruction: str,
        args: List[str],
        current_pc: int,
        labels: Dict[str, int],
        constants: Dict[str, int],
    ) -> List[str]:
        target_token, temp_reg = self.parse_jump_target_args(args, instruction)
        target_resolved = self.resolve_address_operand(target_token, labels, constants, instruction)
        if target_resolved.value is None:
            raise ValueError(f"{instruction} could not resolve operand {target_token}")

        total_size = self.estimate_unsigned_gt_target_size(instruction, args, current_pc, labels, constants)
        skip_addr = (current_pc + total_size) & 0xFFFF

        emitted: List[str] = []
        skip_low = skip_addr & 0xFF
        skip_high = (skip_addr >> 8) & 0xFF
        emitted.extend(self.emit_load_byte(temp_reg, skip_low))
        emitted.append(self.encoder.encode_mov("PRL", temp_reg))
        if skip_high == 0:
            emitted.append(self.encoder.encode_mov("PRH", "ZERO"))
        else:
            emitted.extend(self.emit_load_byte(temp_reg, skip_high))
            emitted.append(self.encoder.encode_mov("PRH", temp_reg))

        emitted.append(self.encoder.encode_jump("JCC"))
        emitted.append(self.encoder.encode_jump("JEQ"))

        target_value = target_resolved.value & 0xFFFF
        target_low = target_value & 0xFF
        target_high = (target_value >> 8) & 0xFF
        emitted.extend(self.emit_load_byte(temp_reg, target_low))
        emitted.append(self.encoder.encode_mov("PRL", temp_reg))
        if target_high == 0:
            emitted.append(self.encoder.encode_mov("PRH", "ZERO"))
        else:
            emitted.extend(self.emit_load_byte(temp_reg, target_high))
            emitted.append(self.encoder.encode_mov("PRH", temp_reg))
        emitted.append(self.encoder.encode_jump("JMP"))
        return emitted

    def estimate_size(
        self,
        instruction: str,
        args: List[str],
        current_pc: int,
        labels: Dict[str, int],
        constants: Dict[str, int],
    ) -> Optional[int]:
        if instruction == "CALL":
            return self.estimate_absolute_transfer_size(instruction, args, labels, constants, final_op_size=1)

        if instruction == "JMPA":
            return self.estimate_absolute_transfer_size(instruction, args, labels, constants, final_op_size=1)

        if instruction in self.jump_conditions and args:
            return self.estimate_jump_with_target_size(instruction, args, labels, constants, [instruction])

        if instruction == "JLE":
            if args:
                return self.estimate_jump_with_target_size(instruction, args, labels, constants, ["JEQ", "JLT"])
            return 2

        if instruction == "JGE":
            if args:
                return self.estimate_jump_with_target_size(instruction, args, labels, constants, ["JEQ", "JGT"])
            return 2

        if instruction == "JLEU":
            if args:
                return self.estimate_jump_with_target_size(instruction, args, labels, constants, ["JCC", "JEQ"])
            return 2

        if instruction == "JGTU":
            if not args:
                raise ValueError("JGTU requires an explicit target operand under the current ISA")
            return self.estimate_unsigned_gt_target_size(instruction, args, current_pc, labels, constants)

        if instruction == "RET":
            self.parse_ret_args(args)
            return 3

        if instruction == "PUSHI":
            value_token, temp_reg = self.parse_pushi_args(args)
            resolved = self.helper.resolve_value(value_token, labels, constants, allow_unresolved=True)
            if resolved.value is None:
                return 3
            if resolved.sliced and resolved.width != 8:
                raise ValueError("PUSHI sliced operands must be exactly 8 bits wide")
            byte_value = resolved.value & 0xFF
            return self.estimate_load_byte_size(byte_value) + 1

        if instruction == "PUSHSTR":
            string_token, trailing_values, _ = self.parse_pushstr_args(args)
            literal = self.parse_string_literal(string_token, "PUSHSTR")
            size = 0
            for token in trailing_values:
                size += self.estimate_value_load_size(token, labels, constants, "PUSHSTR") + 1
            for ch in literal:
                size += self.estimate_load_byte_size(ord(ch)) + 1
            return size

        return None

    def emit(
        self,
        parsed: "ParsedLine",
        instruction: str,
        args: List[str],
        current_pc: int,
        labels: Dict[str, int],
        constants: Dict[str, int],
    ) -> Optional[List[str]]:
        if instruction == "CALL":
            return self.emit_absolute_transfer(instruction, args, labels, constants, final_op="JAL")

        if instruction == "JMPA":
            return self.emit_absolute_transfer(instruction, args, labels, constants, final_op="JMP")

        if instruction in self.jump_conditions and args:
            return self.emit_jump_with_target(instruction, args, labels, constants, [instruction])

        if instruction == "JLE":
            if args:
                return self.emit_jump_with_target(instruction, args, labels, constants, ["JEQ", "JLT"])
            return [
                self.encoder.encode_jump("JEQ"),
                self.encoder.encode_jump("JLT"),
            ]

        if instruction == "JGE":
            if args:
                return self.emit_jump_with_target(instruction, args, labels, constants, ["JEQ", "JGT"])
            return [
                self.encoder.encode_jump("JEQ"),
                self.encoder.encode_special("JGT"),
            ]

        if instruction == "JLEU":
            if args:
                return self.emit_jump_with_target(instruction, args, labels, constants, ["JCC", "JEQ"])
            return [
                self.encoder.encode_jump("JCC"),
                self.encoder.encode_jump("JEQ"),
            ]

        if instruction == "JGTU":
            if not args:
                raise ValueError("JGTU requires an explicit target operand under the current ISA")
            return self.emit_unsigned_gt_target(instruction, args, current_pc, labels, constants)

        if instruction == "RET":
            ret_mode = self.parse_ret_args(args)
            if ret_mode == "LR":
                return [
                    self.encoder.encode_mov("PRL", "LRL"),
                    self.encoder.encode_mov("PRH", "LRH"),
                    self.encoder.encode_jump("JMP"),
                ]
            return [
                self.encoder.encode_pop("PRH"),
                self.encoder.encode_pop("PRL"),
                self.encoder.encode_jump("JMP"),
            ]

        if instruction == "PUSHI":
            value_token, temp_reg = self.parse_pushi_args(args)
            pseudo_parsed = parsed
            emitted = self.helper.emit_ldi(pseudo_parsed, [temp_reg, value_token], labels, constants)
            emitted.append(self.encoder.encode_push_source(temp_reg))
            return emitted

        if instruction == "PUSHSTR":
            string_token, trailing_values, temp_reg = self.parse_pushstr_args(args)
            literal = self.parse_string_literal(string_token, "PUSHSTR")
            emitted: List[str] = []

            for token in reversed(trailing_values):
                emitted.extend(self.helper.emit_ldi(parsed, [temp_reg, token], labels, constants))
                emitted.append(self.encoder.encode_push_source(temp_reg))

            for ch in reversed(literal):
                char_token = repr(ch)
                emitted.extend(self.helper.emit_ldi(parsed, [temp_reg, char_token], labels, constants))
                emitted.append(self.encoder.encode_push_source(temp_reg))

            return emitted

        return None
