"""
AssemblyHelper: assembler/disassembler for the final ArniComp ISA.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
import json
import os
import re
from typing import Dict, List, Optional, Tuple


CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "config.json")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

DESTINATIONS = {name.upper(): bits for name, bits in config["destinations"].items()}
SOURCES = {name.upper(): bits for name, bits in config["sources"].items()}
JUMP_CONDITIONS = {name.upper(): bits for name, bits in config["jump_conditions"].items()}
JUMP_ALIASES = {name.upper(): target.upper() for name, target in config["jump_aliases"].items()}
COMMENT_CHAR = config["special_chars"]["comment"]
LABEL_CHAR = config["special_chars"]["label"]
CONSTANT_KEYWORD = config["keywords"]["constant"]
SLICE_RE = re.compile(r"^(?P<base>.+?)\[(?P<hi>\d+):(?P<lo>\d+)\]$")


@dataclass(frozen=True)
class SourceLine:
    line_number: int
    text: str


@dataclass(frozen=True)
class ParsedLine:
    line_number: int
    raw_line: str
    instruction: str
    args: List[str]


@dataclass(frozen=True)
class ResolvedValue:
    raw_text: str
    value: Optional[int]
    kind: str
    sliced: bool = False
    slice_hi: Optional[int] = None
    slice_lo: Optional[int] = None

    @property
    def width(self) -> Optional[int]:
        if not self.sliced or self.slice_hi is None or self.slice_lo is None:
            return None
        return self.slice_hi - self.slice_lo + 1


class InstructionEncoder:
    """Encode final ISA instructions to 8-bit binary strings."""

    @staticmethod
    def encode_ldl(dest: str, immediate: int) -> str:
        if dest not in {"RA", "RD"}:
            raise ValueError("LDL destination must be RA or RD")
        if not (0 <= immediate <= 31):
            raise ValueError(f"LDL immediate value {immediate} out of range (0-31)")
        return f"11{1 if dest == 'RD' else 0}{immediate:05b}"

    @staticmethod
    def encode_ldh(dest: str, immediate: int) -> str:
        if dest not in {"RA", "RD"}:
            raise ValueError("LDH destination must be RA or RD")
        if not (0 <= immediate <= 7):
            raise ValueError(f"LDH immediate value {immediate} out of range (0-7)")
        return f"0011{1 if dest == 'RD' else 0}{immediate:03b}"

    @staticmethod
    def encode_mov(dest: str, src: str) -> str:
        if dest not in DESTINATIONS:
            raise ValueError(f"Invalid destination register: {dest}")
        if src not in SOURCES:
            raise ValueError(f"Invalid source register: {src}")
        return f"10{DESTINATIONS[dest]}{SOURCES[src]}"

    @staticmethod
    def encode_source_op(operation: str, src: str) -> str:
        if src not in SOURCES:
            raise ValueError(f"Invalid source register for {operation}: {src}")

        prefixes = {
            "ADD": "01000",
            "ADC": "01010",
            "NOT": "01011",
            "SUB": "01100",
            "SBC": "01110",
            "CMP": "01111",
            "XOR": "00001",
            "AND": "00010",
            "PUSH": "00100",
        }
        if operation not in prefixes:
            raise ValueError(f"Unknown source-form instruction: {operation}")
        return f"{prefixes[operation]}{SOURCES[src]}"

    @staticmethod
    def encode_immediate_op(operation: str, immediate: int) -> str:
        if not (0 <= immediate <= 7):
            raise ValueError(f"{operation} immediate value {immediate} out of range (0-7)")
        prefixes = {
            "ADDI": "01001",
            "SUBI": "01101",
        }
        if operation not in prefixes:
            raise ValueError(f"Unknown immediate instruction: {operation}")
        return f"{prefixes[operation]}{immediate:03b}"

    @staticmethod
    def encode_jump(condition: str) -> str:
        if condition not in JUMP_CONDITIONS:
            raise ValueError(f"Unknown jump condition: {condition}")
        return f"00011{JUMP_CONDITIONS[condition]}"

    @staticmethod
    def encode_pop(dest: str) -> str:
        if dest not in DESTINATIONS:
            raise ValueError(f"Invalid destination register for POP: {dest}")
        return f"00101{DESTINATIONS[dest]}"

    @staticmethod
    def encode_special(instruction: str, immediate: Optional[int] = None) -> str:
        if instruction == "NOP":
            return "00000000"
        if instruction == "HLT":
            return "00000001"
        if instruction == "JGT":
            return "00000110"
        if instruction == "JAL":
            return "00000111"
        if instruction == "INC":
            if immediate not in {1, 2}:
                raise ValueError("INC only accepts #1 or #2")
            return f"0000001{immediate - 1}"
        if instruction == "DEC":
            if immediate not in {1, 2}:
                raise ValueError("DEC only accepts #1 or #2")
            return f"0000010{immediate - 1}"
        raise ValueError(f"Unknown special instruction: {instruction}")


class AssemblyHelper:
    """Main assembler class for parsing and converting assembly to machine code."""

    def __init__(
        self,
        comment_char: str = COMMENT_CHAR,
        label_char: str = LABEL_CHAR,
        constant_keyword: str = CONSTANT_KEYWORD,
        number_prefix: str = "#",
        constant_prefix: str = "$",
        label_prefix: str = "@",
    ):
        self.comment_char = comment_char
        self.label_char = label_char
        self.constant_keyword = constant_keyword.lower()
        self.number_prefix = number_prefix
        self.constant_prefix = constant_prefix
        self.label_prefix = label_prefix
        self.encoder = InstructionEncoder()
        self.last_warnings: List[str] = []

    def to_decimal(self, value: str) -> int:
        value = value.strip()
        if value.startswith(self.number_prefix):
            value = value[len(self.number_prefix):]
        if value.startswith(("0x", "0X")):
            return int(value[2:], 16)
        if value.startswith(("0b", "0B")):
            return int(value[2:], 2)
        return int(value)

    def try_parse_char_literal(self, token: str) -> Optional[int]:
        token = token.strip()
        if token.startswith(self.number_prefix):
            token = token[len(self.number_prefix) :].strip()

        if len(token) < 2 or token[0] not in {"'", '"'} or token[-1] != token[0]:
            return None

        try:
            literal = ast.literal_eval(token)
        except (SyntaxError, ValueError) as exc:
            raise ValueError(f"Invalid character literal: {token}") from exc

        if not isinstance(literal, str) or len(literal) != 1:
            raise ValueError(f"Character literals must contain exactly one character: {token}")

        return ord(literal)

    def evaluate_expression(self, expression: str, variables: Optional[Dict[str, int]] = None) -> int:
        variables = variables or {}
        expression = expression.strip()

        allowed_functions = {
            "MAX": max,
            "MIN": min,
        }

        def eval_node(node: ast.AST) -> int:
            if isinstance(node, ast.Expression):
                return eval_node(node.body)

            if isinstance(node, ast.Constant):
                if isinstance(node.value, int):
                    return int(node.value)
                if isinstance(node.value, str):
                    if len(node.value) != 1:
                        raise ValueError(
                            f"Character literals in expressions must contain exactly one character: {expression}"
                        )
                    return ord(node.value)
                raise ValueError(f"Unsupported constant in expression: {expression}")

            if isinstance(node, ast.Name):
                name = node.id.upper()
                if name in variables:
                    return variables[name]
                raise ValueError(f"Unknown constant in expression: {node.id}")

            if isinstance(node, ast.UnaryOp):
                operand = eval_node(node.operand)
                if isinstance(node.op, ast.UAdd):
                    return operand
                if isinstance(node.op, ast.USub):
                    return -operand
                raise ValueError(f"Unsupported unary operator in expression: {expression}")

            if isinstance(node, ast.BinOp):
                left = eval_node(node.left)
                right = eval_node(node.right)
                if isinstance(node.op, ast.Add):
                    return left + right
                if isinstance(node.op, ast.Sub):
                    return left - right
                if isinstance(node.op, ast.Mult):
                    return left * right
                if isinstance(node.op, (ast.Div, ast.FloorDiv)):
                    if right == 0:
                        raise ValueError("Division by zero in constant expression")
                    return left // right
                if isinstance(node.op, ast.Mod):
                    if right == 0:
                        raise ValueError("Modulo by zero in constant expression")
                    return left % right
                if isinstance(node.op, ast.LShift):
                    return left << right
                if isinstance(node.op, ast.RShift):
                    return left >> right
                if isinstance(node.op, ast.BitOr):
                    return left | right
                if isinstance(node.op, ast.BitAnd):
                    return left & right
                if isinstance(node.op, ast.BitXor):
                    return left ^ right
                raise ValueError(f"Unsupported operator in expression: {expression}")

            if isinstance(node, ast.Call):
                if not isinstance(node.func, ast.Name):
                    raise ValueError(f"Unsupported function call in expression: {expression}")
                func_name = node.func.id.upper()
                if func_name not in allowed_functions:
                    raise ValueError(f"Unsupported function in expression: {node.func.id}")
                args = [eval_node(arg) for arg in node.args]
                return int(allowed_functions[func_name](*args))

            raise ValueError(f"Unsupported expression: {expression}")

        try:
            parsed = ast.parse(expression, mode="eval")
            return eval_node(parsed)
        except SyntaxError as e:
            raise ValueError(f"Invalid constant expression '{expression}': {e.msg}") from e

    def clean_lines(self, lines: List[str]) -> List[SourceLine]:
        cleaned: List[SourceLine] = []
        for index, line in enumerate(lines, start=1):
            if self.comment_char in line:
                line = line[: line.index(self.comment_char)]
            line = line.strip()
            if not line:
                continue
            cleaned.append(SourceLine(index, line))
        return cleaned

    def extract_constants(self, lines: List[SourceLine]) -> Tuple[Dict[str, int], List[SourceLine]]:
        constants: Dict[str, int] = {}
        remaining_lines: List[SourceLine] = []

        for source_line in lines:
            parts = source_line.text.split(None, 2)
            if parts and parts[0].lower() == self.constant_keyword:
                if len(parts) < 3:
                    raise ValueError(
                        f"Error on line {source_line.line_number} ('{source_line.text}'): "
                        "Invalid constant definition"
                    )
                const_name = parts[1].upper()
                const_value = self.evaluate_expression(parts[2], constants)
                constants[const_name] = const_value
            else:
                remaining_lines.append(source_line)

        return constants, remaining_lines

    def is_label_definition(self, text: str) -> bool:
        return text.endswith(self.label_char)

    def parse_instruction(self, line: str) -> Tuple[str, List[str]]:
        parts = line.replace(",", " ").split()
        if not parts:
            raise ValueError("Empty instruction line")
        return parts[0].upper(), [arg.strip() for arg in parts[1:]]

    def parse_source_line(self, source_line: SourceLine) -> ParsedLine:
        instruction, args = self.parse_instruction(source_line.text)
        return ParsedLine(
            line_number=source_line.line_number,
            raw_line=source_line.text,
            instruction=instruction,
            args=args,
        )

    def is_jump_name(self, token: str) -> bool:
        token_upper = token.upper()
        return token_upper in JUMP_CONDITIONS or token_upper in JUMP_ALIASES

    def canonical_jump_name(self, token: str) -> str:
        token_upper = token.upper()
        if token_upper in JUMP_ALIASES:
            return JUMP_ALIASES[token_upper]
        return token_upper

    def normalize_instruction(self, instruction: str, args: List[str]) -> Tuple[str, List[str]]:
        instruction = instruction.upper()
        args = [arg.strip() for arg in args]

        if instruction in JUMP_ALIASES:
            instruction = JUMP_ALIASES[instruction]

        if instruction == "JMP" and len(args) == 1 and self.is_jump_name(args[0]):
            return self.canonical_jump_name(args[0]), []

        if instruction == "CLR":
            if len(args) != 1:
                raise ValueError(f"CLR requires 1 argument, got {len(args)}")
            return "MOV", [args[0], "ZERO"]

        if instruction == "ADD" and len(args) == 1 and self.looks_like_nonzero_immediate(args[0]):
            raise ValueError("ADD does not accept immediate operands; use ADDI instead")

        if instruction == "SUB" and len(args) == 1 and self.looks_like_nonzero_immediate(args[0]):
            raise ValueError("SUB does not accept immediate operands; use SUBI instead")

        return instruction, args

    def looks_like_nonzero_immediate(self, token: str) -> bool:
        stripped = token.strip()
        if stripped.upper() == "ZERO":
            return False
        if stripped in {"0", "#0"}:
            return False
        if stripped.startswith(self.label_prefix):
            return False
        if stripped.startswith(self.constant_prefix):
            return True
        try:
            char_value = self.try_parse_char_literal(stripped)
            if char_value is not None:
                return char_value != 0
            return self.to_decimal(stripped) != 0
        except Exception:
            return stripped.startswith(self.number_prefix)

    def parse_slice(self, token: str) -> Tuple[str, Optional[int], Optional[int]]:
        match = SLICE_RE.match(token.strip())
        if not match:
            return token.strip(), None, None
        hi = int(match.group("hi"))
        lo = int(match.group("lo"))
        if hi < lo:
            raise ValueError(f"Invalid bit slice '{token}': high bit must be >= low bit")
        return match.group("base").strip(), hi, lo

    def resolve_base_value(
        self,
        token: str,
        labels: Dict[str, int],
        constants: Dict[str, int],
        allow_unresolved: bool = False,
    ) -> ResolvedValue:
        token = token.strip()
        token_upper = token.upper()

        if token_upper == "ZERO":
            return ResolvedValue(raw_text=token, value=0, kind="zero")

        char_value = self.try_parse_char_literal(token)
        if char_value is not None:
            return ResolvedValue(raw_text=token, value=char_value, kind="char")

        if token.startswith(self.number_prefix) or re.fullmatch(r"(0[xX][0-9a-fA-F]+|0[bB][01]+|\d+)", token):
            return ResolvedValue(raw_text=token, value=self.to_decimal(token), kind="numeric")

        if token_upper == "0":
            return ResolvedValue(raw_text=token, value=0, kind="zero")

        if token.startswith(self.constant_prefix):
            name = token[len(self.constant_prefix) :].strip().upper()
            if name not in constants:
                raise ValueError(f"Undefined constant reference: {token}")
            return ResolvedValue(raw_text=token, value=constants[name], kind="constant")

        if token.startswith(self.label_prefix):
            name = token[len(self.label_prefix) :].strip().upper()
            if name not in labels:
                if allow_unresolved:
                    return ResolvedValue(raw_text=token, value=None, kind="label")
                raise ValueError(f"Undefined label reference: {token}")
            return ResolvedValue(raw_text=token, value=labels[name], kind="label")

        raise ValueError(f"Unsupported operand value: {token}")

    def resolve_value(
        self,
        token: str,
        labels: Dict[str, int],
        constants: Dict[str, int],
        allow_unresolved: bool = False,
    ) -> ResolvedValue:
        base_token, hi, lo = self.parse_slice(token)
        base_value = self.resolve_base_value(base_token, labels, constants, allow_unresolved=allow_unresolved)

        if hi is None or lo is None:
            return base_value

        if hi < 0 or lo < 0:
            raise ValueError(f"Invalid bit slice '{token}': bit indices must be non-negative")

        if base_value.value is None:
            return ResolvedValue(
                raw_text=token,
                value=None,
                kind=base_value.kind,
                sliced=True,
                slice_hi=hi,
                slice_lo=lo,
            )

        width = hi - lo + 1
        slice_value = (base_value.value >> lo) & ((1 << width) - 1)
        return ResolvedValue(
            raw_text=token,
            value=slice_value,
            kind=base_value.kind,
            sliced=True,
            slice_hi=hi,
            slice_lo=lo,
        )

    def parse_destination(self, token: str, instruction: str) -> str:
        token_upper = token.upper()
        if token_upper not in DESTINATIONS:
            raise ValueError(f"{instruction} destination must be one of {list(DESTINATIONS.keys())}, got {token}")
        return token_upper

    def parse_ra_rd_destination(self, token: str, instruction: str) -> str:
        token_upper = token.upper()
        if token_upper not in {"RA", "RD"}:
            raise ValueError(f"{instruction} destination must be RA or RD, got {token}")
        return token_upper

    def parse_source(self, token: str, instruction: str, allow_zero_alias: bool = True) -> str:
        token_upper = token.upper()
        if allow_zero_alias and token_upper in {"ZERO", "0", "#0"}:
            return "ZERO"
        if token_upper in SOURCES:
            return token_upper
        raise ValueError(f"{instruction} source must be one of {list(SOURCES.keys()) + ['0', '#0']}, got {token}")

    def parse_small_immediate(
        self,
        token: str,
        instruction: str,
        labels: Dict[str, int],
        constants: Dict[str, int],
        min_value: int,
        max_value: int,
        required_width: Optional[int] = None,
    ) -> int:
        resolved = self.resolve_value(token, labels, constants)
        if resolved.value is None:
            raise ValueError(f"{instruction} could not resolve operand {token}")
        if required_width is not None and resolved.sliced and resolved.width != required_width:
            raise ValueError(
                f"{instruction} requires a slice width of {required_width} bits, got "
                f"[{resolved.slice_hi}:{resolved.slice_lo}]"
            )
        if not (min_value <= resolved.value <= max_value):
            raise ValueError(f"{instruction} immediate value {resolved.value} out of range ({min_value}-{max_value})")
        return resolved.value

    def normalize_ldi_args(self, args: List[str]) -> Tuple[str, str]:
        if len(args) == 1:
            return "RA", args[0]
        if len(args) == 2:
            return self.parse_ra_rd_destination(args[0], "LDI"), args[1]
        raise ValueError(f"LDI requires 1 or 2 arguments, got {len(args)}")

    def estimate_instruction_size(
        self,
        instruction: str,
        args: List[str],
        labels: Dict[str, int],
        constants: Dict[str, int],
    ) -> int:
        instruction, args = self.normalize_instruction(instruction, args)

        if instruction == "LDI":
            _, value_token = self.normalize_ldi_args(args)
            resolved = self.resolve_value(value_token, labels, constants, allow_unresolved=True)
            if resolved.value is None:
                return 2
            if resolved.sliced and resolved.width != 8:
                raise ValueError("LDI sliced operands must be exactly 8 bits wide")
            low_byte = resolved.value & 0xFF
            return 1 if low_byte <= 31 else 2

        if instruction == "JLE":
            if args:
                raise ValueError("JLE does not take operands")
            return 2

        if instruction == "JGE":
            if args:
                raise ValueError("JGE does not take operands")
            return 2

        return 1

    def build_labels(self, lines: List[SourceLine], constants: Dict[str, int]) -> Dict[str, int]:
        guess: Dict[str, int] = {}

        for _ in range(32):
            labels: Dict[str, int] = {}
            pc = 0

            for source_line in lines:
                if self.is_label_definition(source_line.text):
                    label_name = source_line.text[:-1].strip().upper()
                    if label_name in labels:
                        raise ValueError(
                            f"Error on line {source_line.line_number} ('{source_line.text}'): "
                            f"Duplicate label definition: {label_name}"
                        )
                    labels[label_name] = pc
                    continue

                parsed = self.parse_source_line(source_line)
                try:
                    pc += self.estimate_instruction_size(parsed.instruction, parsed.args, guess, constants)
                except Exception as e:
                    raise ValueError(f"Error on line {parsed.line_number} ('{parsed.raw_line}'): {e}")

            if labels == guess:
                return labels
            guess = labels

        raise ValueError("Label address stabilization failed after 32 passes")

    def emit_ldi(self, parsed: ParsedLine, args: List[str], labels: Dict[str, int], constants: Dict[str, int]) -> List[str]:
        dest, value_token = self.normalize_ldi_args(args)
        resolved = self.resolve_value(value_token, labels, constants)
        if resolved.value is None:
            raise ValueError(f"LDI could not resolve operand {value_token}")
        if resolved.sliced and resolved.width != 8:
            raise ValueError("LDI sliced operands must be exactly 8 bits wide")

        if not resolved.sliced and resolved.value > 0xFF:
            self.last_warnings.append(
                f"Line {parsed.line_number} ('{parsed.raw_line}'): "
                f"LDI operand resolves to 0x{resolved.value:X}; only the low byte 0x{resolved.value & 0xFF:02X} is used."
            )

        byte_value = resolved.value & 0xFF
        if byte_value <= 31:
            return [self.encoder.encode_ldl(dest, byte_value)]

        return [
            self.encoder.encode_ldl(dest, byte_value & 0x1F),
            self.encoder.encode_ldh(dest, (byte_value >> 5) & 0x07),
        ]

    def encode_actual_instruction(
        self,
        instruction: str,
        args: List[str],
        labels: Dict[str, int],
        constants: Dict[str, int],
    ) -> str:
        if instruction == "NOP":
            if args:
                raise ValueError("NOP does not take arguments")
            return self.encoder.encode_special("NOP")

        if instruction == "HLT":
            if args:
                raise ValueError("HLT does not take arguments")
            return self.encoder.encode_special("HLT")

        if instruction == "JGT":
            if args:
                raise ValueError("JGT does not take arguments")
            return self.encoder.encode_special("JGT")

        if instruction == "JAL":
            if args:
                raise ValueError("JAL does not take arguments")
            return self.encoder.encode_special("JAL")

        if instruction == "INC":
            if len(args) != 1:
                raise ValueError(f"INC requires 1 argument, got {len(args)}")
            resolved = self.resolve_value(args[0], labels, constants)
            if resolved.value not in {1, 2}:
                raise ValueError("INC only accepts #1 or #2")
            value = resolved.value
            return self.encoder.encode_special("INC", value)

        if instruction == "DEC":
            if len(args) != 1:
                raise ValueError(f"DEC requires 1 argument, got {len(args)}")
            resolved = self.resolve_value(args[0], labels, constants)
            if resolved.value not in {1, 2}:
                raise ValueError("DEC only accepts #1 or #2")
            value = resolved.value
            return self.encoder.encode_special("DEC", value)

        if instruction == "LDL":
            if len(args) != 2:
                raise ValueError(f"LDL requires 2 arguments, got {len(args)}")
            dest = self.parse_ra_rd_destination(args[0], "LDL")
            immediate = self.parse_small_immediate(args[1], "LDL", labels, constants, 0, 31, required_width=5)
            return self.encoder.encode_ldl(dest, immediate)

        if instruction == "LDH":
            if len(args) != 2:
                raise ValueError(f"LDH requires 2 arguments, got {len(args)}")
            dest = self.parse_ra_rd_destination(args[0], "LDH")
            immediate = self.parse_small_immediate(args[1], "LDH", labels, constants, 0, 7, required_width=3)
            return self.encoder.encode_ldh(dest, immediate)

        if instruction == "MOV":
            if len(args) != 2:
                raise ValueError(f"MOV requires 2 arguments, got {len(args)}")
            dest = self.parse_destination(args[0], "MOV")
            src = self.parse_source(args[1], "MOV")
            return self.encoder.encode_mov(dest, src)

        if instruction in {"ADD", "ADC", "NOT", "SUB", "SBC", "CMP", "XOR", "AND", "PUSH"}:
            if len(args) != 1:
                raise ValueError(f"{instruction} requires 1 argument, got {len(args)}")
            src = self.parse_source(args[0], instruction)
            return self.encoder.encode_source_op(instruction, src)

        if instruction in {"ADDI", "SUBI"}:
            if len(args) != 1:
                raise ValueError(f"{instruction} requires 1 argument, got {len(args)}")
            immediate = self.parse_small_immediate(args[0], instruction, labels, constants, 0, 7)
            return self.encoder.encode_immediate_op(instruction, immediate)

        if instruction == "POP":
            if len(args) != 1:
                raise ValueError(f"POP requires 1 argument, got {len(args)}")
            dest = self.parse_destination(args[0], "POP")
            return self.encoder.encode_pop(dest)

        if instruction in JUMP_CONDITIONS:
            if args:
                raise ValueError(f"{instruction} does not take operands")
            return self.encoder.encode_jump(instruction)

        raise ValueError(f"Unknown instruction: {instruction}")

    def emit_instruction(self, parsed: ParsedLine, labels: Dict[str, int], constants: Dict[str, int]) -> List[str]:
        instruction, args = self.normalize_instruction(parsed.instruction, parsed.args)

        if instruction == "LDI":
            return self.emit_ldi(parsed, args, labels, constants)

        if instruction == "JLE":
            if args:
                raise ValueError("JLE does not take operands")
            return [
                self.encoder.encode_jump("JEQ"),
                self.encoder.encode_jump("JLT"),
            ]

        if instruction == "JGE":
            if args:
                raise ValueError("JGE does not take operands")
            return [
                self.encoder.encode_jump("JEQ"),
                self.encoder.encode_special("JGT"),
            ]

        return [self.encode_actual_instruction(instruction, args, labels, constants)]

    def convert_to_machine_code(self, raw_lines: List[str]) -> Tuple[List[str], Dict[str, int], Dict[str, int]]:
        self.last_warnings = []

        lines = self.clean_lines(raw_lines)
        constants, lines = self.extract_constants(lines)
        labels = self.build_labels(lines, constants)

        binary_lines: List[str] = []
        for source_line in lines:
            if self.is_label_definition(source_line.text):
                continue

            parsed = self.parse_source_line(source_line)
            try:
                encoded_lines = self.emit_instruction(parsed, labels, constants)
                binary_lines.extend(f"{binary}\n" for binary in encoded_lines)
            except Exception as e:
                raise ValueError(f"Error on line {parsed.line_number} ('{parsed.raw_line}'): {e}")

        return binary_lines, labels, constants

    def disassemble(self, binary_code: str) -> str:
        binary_code = binary_code.strip()
        if len(binary_code) != 8 or any(bit not in "01" for bit in binary_code):
            raise ValueError(f"Invalid binary code: {binary_code}")

        if binary_code.startswith("11"):
            dest = "RD" if binary_code[2] == "1" else "RA"
            immediate = int(binary_code[3:], 2)
            return f"LDL {dest}, #{immediate}"

        if binary_code.startswith("10"):
            dest_bits = binary_code[2:5]
            src_bits = binary_code[5:8]
            dest = next((name for name, bits in DESTINATIONS.items() if bits == dest_bits), None)
            src = next((name for name, bits in SOURCES.items() if bits == src_bits), None)
            if not dest or not src:
                return f"??? {binary_code}"
            return f"MOV {dest}, {src}"

        if binary_code == "00000000":
            return "NOP"
        if binary_code == "00000001":
            return "HLT"
        if binary_code == "00000110":
            return "JGT"
        if binary_code == "00000111":
            return "JAL"
        if binary_code.startswith("0000001"):
            return f"INC #{int(binary_code[-1], 2) + 1}"
        if binary_code.startswith("0000010"):
            return f"DEC #{int(binary_code[-1], 2) + 1}"
        if binary_code.startswith("00011"):
            cond_bits = binary_code[5:8]
            name = next((mnemonic for mnemonic, bits in JUMP_CONDITIONS.items() if bits == cond_bits), None)
            return name or f"??? {binary_code}"
        if binary_code.startswith("00100"):
            src_bits = binary_code[5:8]
            src = next((name for name, bits in SOURCES.items() if bits == src_bits), None)
            return f"PUSH {src}" if src else f"??? {binary_code}"
        if binary_code.startswith("00101"):
            dest_bits = binary_code[5:8]
            dest = next((name for name, bits in DESTINATIONS.items() if bits == dest_bits), None)
            return f"POP {dest}" if dest else f"??? {binary_code}"
        if binary_code.startswith("0011"):
            dest = "RD" if binary_code[4] == "1" else "RA"
            immediate = int(binary_code[5:8], 2)
            return f"LDH {dest}, #{immediate}"

        source_forms = {
            "01000": "ADD",
            "01010": "ADC",
            "01011": "NOT",
            "01100": "SUB",
            "01110": "SBC",
            "01111": "CMP",
            "00001": "XOR",
            "00010": "AND",
        }
        for prefix, mnemonic in source_forms.items():
            if binary_code.startswith(prefix):
                src_bits = binary_code[5:8]
                src = next((name for name, bits in SOURCES.items() if bits == src_bits), None)
                return f"{mnemonic} {src}" if src else f"??? {binary_code}"

        if binary_code.startswith("01001"):
            return f"ADDI #{int(binary_code[5:8], 2)}"
        if binary_code.startswith("01101"):
            return f"SUBI #{int(binary_code[5:8], 2)}"

        return f"??? {binary_code}"
