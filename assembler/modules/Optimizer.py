from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Dict, List, Optional, Sequence, Tuple, TYPE_CHECKING


if TYPE_CHECKING:
    from .AssemblyHelper import AssemblyHelper, ParsedLine, SourceLine


TARGET_JUMP_INSTRUCTIONS = {"JEQ", "JNE", "JCS", "JCC", "JMI", "JVS", "JLT", "JMP"}
VARIANT_ORDER = {"long": 2, "short": 1, "zero": 0}


@dataclass(frozen=True)
class TransferSpec:
    pointer_reg: str
    temp_reg: str
    source_kind: str
    byte_part: str


@dataclass
class LayoutState:
    labels: Dict[str, int]
    starts: List[int]
    sizes: List[int]


@dataclass
class LinePlanNode:
    source_line: "SourceLine"
    label_name: Optional[str]
    instruction_text: str
    parsed: Optional["ParsedLine"]
    base_min_size: Optional[int] = None

    def estimate_current_size(
        self,
        helper: "AssemblyHelper",
        current_pc: int,
        labels: Dict[str, int],
        constants: Dict[str, int],
    ) -> int:
        if self.parsed is None:
            return 0
        return helper.estimate_instruction_size(self.parsed.instruction, self.parsed.args, current_pc, labels, constants)

    def estimate_min_size(
        self,
        helper: "AssemblyHelper",
        current_pc: int,
        labels: Dict[str, int],
        constants: Dict[str, int],
    ) -> int:
        if self.parsed is None:
            return 0
        return helper.estimate_min_instruction_size(self.parsed.instruction, self.parsed.args, current_pc, labels, constants)

    def emit(
        self,
        helper: "AssemblyHelper",
        current_pc: int,
        labels: Dict[str, int],
        constants: Dict[str, int],
    ) -> List[str]:
        if self.parsed is None:
            return []
        return helper.emit_instruction(self.parsed, current_pc, labels, constants)


@dataclass
class OptimizableMacroNode(LinePlanNode):
    macro_kind: str = ""
    target_token: str = ""
    temp_reg: str = "RA"
    final_ops: List[str] = field(default_factory=list)
    transfer_specs: List[TransferSpec] = field(default_factory=list)
    selected_variants: List[str] = field(default_factory=list)
    resolved_mode: str = "unknown"
    resolved_name: Optional[str] = None
    resolved_exact_value: Optional[int] = None

    def estimate_current_size(
        self,
        helper: "AssemblyHelper",
        current_pc: int,
        labels: Dict[str, int],
        constants: Dict[str, int],
    ) -> int:
        del current_pc, labels, constants
        return len(self.final_ops) + sum(self._variant_size(variant) for variant in self.selected_variants)

    def estimate_min_size(
        self,
        helper: "AssemblyHelper",
        current_pc: int,
        labels: Dict[str, int],
        constants: Dict[str, int],
    ) -> int:
        del current_pc, labels, constants
        return len(self.final_ops) + len(self.transfer_specs) * helper.macro_expander.minimum_address_byte_transfer_size()

    def emit(
        self,
        helper: "AssemblyHelper",
        current_pc: int,
        labels: Dict[str, int],
        constants: Dict[str, int],
    ) -> List[str]:
        emitted: List[str] = []
        current_size = self.estimate_current_size(helper, current_pc, labels, constants)
        skip_addr = (current_pc + current_size) & 0xFFFF if self.macro_kind == "JGTU_TARGET" else None
        target_value = self._resolve_target_value(helper, labels, constants)

        for spec, variant in zip(self.transfer_specs, self.selected_variants):
            byte_value = self._resolve_transfer_byte(
                helper,
                spec,
                skip_addr,
                labels,
                constants,
                target_value=target_value,
            )
            emitted.extend(
                helper.macro_expander.emit_address_byte_transfer_variant(
                    spec.pointer_reg,
                    spec.temp_reg,
                    byte_value,
                    variant,
                )
            )

        for op in self.final_ops:
            emitted.append(self._encode_final_op(helper, op))
        return emitted

    def try_relax(
        self,
        helper: "AssemblyHelper",
        current_state: LayoutState,
        min_state: LayoutState,
        node_index: int,
        constants: Dict[str, int],
    ) -> bool:
        changed = False
        start_min = min_state.starts[node_index]
        start_max = current_state.starts[node_index]
        skip_interval = (
            (start_min + self.estimate_min_size(helper, start_min, min_state.labels, constants)) & 0xFFFF,
            (start_max + self.estimate_current_size(helper, start_max, current_state.labels, constants)) & 0xFFFF,
        )

        target_interval = self._resolve_target_interval(helper, current_state, min_state, constants)

        for index, spec in enumerate(self.transfer_specs):
            interval = skip_interval if spec.source_kind == "skip" else target_interval
            if interval is None:
                continue
            safe_variant = self._best_safe_variant_for_interval(interval, spec.byte_part)
            if safe_variant is None:
                continue
            if VARIANT_ORDER[safe_variant] < VARIANT_ORDER[self.selected_variants[index]]:
                self.selected_variants[index] = safe_variant
                changed = True
        return changed

    def _current_size_without_pc(self, helper: "AssemblyHelper") -> int:
        return len(self.final_ops) + sum(self._variant_size(variant) for variant in self.selected_variants)

    def _resolve_target_value(
        self,
        helper: "AssemblyHelper",
        labels: Dict[str, int],
        constants: Dict[str, int],
    ) -> int:
        resolved = helper.macro_expander.resolve_address_operand(
            self.target_token,
            labels,
            constants,
            self.macro_kind,
        )
        if resolved.value is None:
            raise ValueError(f"{self.macro_kind} could not resolve operand {self.target_token}")
        return resolved.value & 0xFFFF

    def _resolve_transfer_byte(
        self,
        helper: "AssemblyHelper",
        spec: TransferSpec,
        skip_addr: Optional[int],
        labels: Dict[str, int],
        constants: Dict[str, int],
        *,
        target_value: Optional[int] = None,
    ) -> int:
        if spec.source_kind == "skip":
            if skip_addr is None:
                raise ValueError("Skip-address transfer requested without skip address")
            value = skip_addr
        else:
            if target_value is None:
                value = self._resolve_target_value(helper, labels, constants)
            else:
                value = target_value
        if spec.byte_part == "low":
            return value & 0xFF
        return (value >> 8) & 0xFF

    def _resolve_target_interval(
        self,
        helper: "AssemblyHelper",
        current_state: LayoutState,
        min_state: LayoutState,
        constants: Dict[str, int],
    ) -> Optional[Tuple[int, int]]:
        if self.resolved_mode == "constant":
            if self.resolved_exact_value is None:
                return None
            return self.resolved_exact_value, self.resolved_exact_value

        if self.resolved_mode == "label":
            if self.resolved_name is None:
                return None
            if self.resolved_name not in current_state.labels or self.resolved_name not in min_state.labels:
                return None
            return min_state.labels[self.resolved_name], current_state.labels[self.resolved_name]

        if self.resolved_mode == "label_expr":
            try:
                max_resolved = helper.macro_expander.resolve_address_operand(
                    self.target_token,
                    current_state.labels,
                    constants,
                    self.macro_kind,
                )
                min_resolved = helper.macro_expander.resolve_address_operand(
                    self.target_token,
                    min_state.labels,
                    constants,
                    self.macro_kind,
                )
            except Exception:
                return None
            if max_resolved.value is None or min_resolved.value is None:
                return None
            lower = min(min_resolved.value & 0xFFFF, max_resolved.value & 0xFFFF)
            upper = max(min_resolved.value & 0xFFFF, max_resolved.value & 0xFFFF)
            return lower, upper

        return None

    def _best_safe_variant_for_interval(
        self,
        interval: Tuple[int, int],
        byte_part: str,
    ) -> Optional[str]:
        lower, upper = interval
        if lower > upper:
            lower, upper = upper, lower

        if self._interval_byte_always_zero(lower, upper, byte_part):
            return "zero"
        if self._interval_byte_always_short(lower, upper, byte_part):
            return "short"
        return "long"

    def _interval_byte_always_zero(self, lower: int, upper: int, byte_part: str) -> bool:
        if byte_part == "high":
            return upper < 0x0100

        return (lower >> 8) == (upper >> 8) and (lower & 0xFF) == 0 and (upper & 0xFF) == 0

    def _interval_byte_always_short(self, lower: int, upper: int, byte_part: str) -> bool:
        if byte_part == "high":
            return ((upper >> 8) & 0xFF) <= 31

        if (lower >> 8) != (upper >> 8):
            return False
        return (upper & 0xFF) <= 31

    def _encode_final_op(self, helper: "AssemblyHelper", op: str) -> str:
        if op == "JGT":
            return helper.encoder.encode_special("JGT")
        if op == "JAL":
            return helper.encoder.encode_special("JAL")
        return helper.encoder.encode_jump(op)

    def _variant_size(self, variant: str) -> int:
        if variant == "long":
            return 3
        if variant == "short":
            return 2
        if variant == "zero":
            return 1
        raise ValueError(f"Unknown transfer variant: {variant}")


class Optimizer:
    def __init__(self, helper: "AssemblyHelper") -> None:
        self.helper = helper

    def optimize(
        self,
        lines: List["SourceLine"],
        constants: Dict[str, int],
    ) -> Tuple[List[str], Dict[str, int], List[Tuple["SourceLine", int, List[str]]]]:
        nodes = self._build_nodes(lines, constants)

        for _ in range(max(len(nodes), 1) * 4):
            current_state = self._stabilize_layout(nodes, constants, minimum=False)
            min_state = self._stabilize_layout(nodes, constants, minimum=True)
            changed = False
            for index, node in enumerate(nodes):
                if isinstance(node, OptimizableMacroNode):
                    changed |= node.try_relax(self.helper, current_state, min_state, index, constants)
            if not changed:
                break

        final_state = self._stabilize_layout(nodes, constants, minimum=False)
        binary_lines: List[str] = []
        listing_rows: List[Tuple["SourceLine", int, List[str]]] = []
        for index, node in enumerate(nodes):
            start_pc = final_state.starts[index]
            emitted = node.emit(self.helper, start_pc, final_state.labels, constants)
            binary_lines.extend(f"{byte}\n" for byte in emitted)
            if emitted:
                listing_rows.append((node.source_line, start_pc, emitted))

        return binary_lines, final_state.labels, listing_rows

    def _build_nodes(self, lines: List["SourceLine"], constants: Dict[str, int]) -> List[LinePlanNode]:
        nodes: List[LinePlanNode] = []
        for source_line in lines:
            label_name, instruction_text = self.helper.split_label_prefix(source_line.text)
            parsed = None
            if instruction_text:
                parsed = self.helper.parse_source_line(source_line)

            if parsed is None:
                nodes.append(
                    LinePlanNode(
                        source_line=source_line,
                        label_name=label_name,
                        instruction_text=instruction_text,
                        parsed=None,
                    )
                )
                continue

            node = self._try_build_optimizable_node(source_line, label_name, instruction_text, parsed, constants)
            if node is None:
                node = LinePlanNode(
                    source_line=source_line,
                    label_name=label_name,
                    instruction_text=instruction_text,
                    parsed=parsed,
                )
            nodes.append(node)

        return nodes

    def _try_build_optimizable_node(
        self,
        source_line: "SourceLine",
        label_name: Optional[str],
        instruction_text: str,
        parsed: "ParsedLine",
        constants: Dict[str, int],
    ) -> Optional[OptimizableMacroNode]:
        instruction, args = self.helper.normalize_instruction(parsed.instruction, parsed.args)
        macro = self.helper.macro_expander

        macro_kind: Optional[str] = None
        target_token = ""
        temp_reg = "RA"
        final_ops: List[str] = []
        transfer_specs: List[TransferSpec] = []

        if instruction == "CALL":
            target_token, temp_reg = macro.parse_call_args(args)
            final_ops = ["JAL"]
            transfer_specs = [
                TransferSpec("PRL", temp_reg, "target", "low"),
                TransferSpec("PRH", temp_reg, "target", "high"),
            ]
            macro_kind = "CALL"
        elif instruction == "JMPA":
            target_token, temp_reg = macro.parse_jumpa_args(args)
            final_ops = ["JMP"]
            transfer_specs = [
                TransferSpec("PRL", temp_reg, "target", "low"),
                TransferSpec("PRH", temp_reg, "target", "high"),
            ]
            macro_kind = "JMPA"
        elif instruction in TARGET_JUMP_INSTRUCTIONS and args:
            target_token, temp_reg = macro.parse_jump_target_args(args, instruction)
            final_ops = [instruction]
            transfer_specs = [
                TransferSpec("PRL", temp_reg, "target", "low"),
                TransferSpec("PRH", temp_reg, "target", "high"),
            ]
            macro_kind = f"{instruction}_TARGET"
        elif instruction == "JLE" and args:
            target_token, temp_reg = macro.parse_jump_target_args(args, instruction)
            final_ops = ["JEQ", "JLT"]
            transfer_specs = [
                TransferSpec("PRL", temp_reg, "target", "low"),
                TransferSpec("PRH", temp_reg, "target", "high"),
            ]
            macro_kind = "JLE_TARGET"
        elif instruction == "JGE" and args:
            target_token, temp_reg = macro.parse_jump_target_args(args, instruction)
            final_ops = ["JEQ", "JGT"]
            transfer_specs = [
                TransferSpec("PRL", temp_reg, "target", "low"),
                TransferSpec("PRH", temp_reg, "target", "high"),
            ]
            macro_kind = "JGE_TARGET"
        elif instruction == "JLEU" and args:
            target_token, temp_reg = macro.parse_jump_target_args(args, instruction)
            final_ops = ["JCC", "JEQ"]
            transfer_specs = [
                TransferSpec("PRL", temp_reg, "target", "low"),
                TransferSpec("PRH", temp_reg, "target", "high"),
            ]
            macro_kind = "JLEU_TARGET"
        elif instruction == "JGTU" and args:
            target_token, temp_reg = macro.parse_jump_target_args(args, instruction)
            final_ops = ["JCC", "JEQ", "JMP"]
            transfer_specs = [
                TransferSpec("PRL", temp_reg, "skip", "low"),
                TransferSpec("PRH", temp_reg, "skip", "high"),
                TransferSpec("PRL", temp_reg, "target", "low"),
                TransferSpec("PRH", temp_reg, "target", "high"),
            ]
            macro_kind = "JGTU_TARGET"
        else:
            return None

        resolved_mode, resolved_name, resolved_exact_value = self._classify_target_reference(target_token, constants)
        return OptimizableMacroNode(
            source_line=source_line,
            label_name=label_name,
            instruction_text=instruction_text,
            parsed=parsed,
            macro_kind=macro_kind,
            target_token=target_token,
            temp_reg=temp_reg,
            final_ops=final_ops,
            transfer_specs=transfer_specs,
            selected_variants=["long"] * len(transfer_specs),
            resolved_mode=resolved_mode,
            resolved_name=resolved_name,
            resolved_exact_value=resolved_exact_value,
        )

    def _classify_target_reference(
        self,
        token: str,
        constants: Dict[str, int],
    ) -> Tuple[str, Optional[str], Optional[int]]:
        stripped = token.strip()

        direct_label = re.fullmatch(r"@([A-Za-z_][A-Za-z0-9_]*)", stripped)
        if direct_label:
            return "label", direct_label.group(1).upper(), None

        bare_label = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)", stripped)
        if bare_label:
            return "label", bare_label.group(1).upper(), None

        try:
            resolved = self.helper.resolve_value(stripped, {}, constants)
        except Exception:
            resolved = None
        if resolved is not None and resolved.value is not None:
            return "constant", None, resolved.value & 0xFFFF

        if "@" in stripped:
            return "label_expr", None, None

        return "unknown", None, None

    def _stabilize_layout(
        self,
        nodes: Sequence[LinePlanNode],
        constants: Dict[str, int],
        *,
        minimum: bool,
    ) -> LayoutState:
        guess: Dict[str, int] = {}
        for _ in range(32):
            labels: Dict[str, int] = {}
            starts: List[int] = []
            sizes: List[int] = []
            pc = 0

            for node in nodes:
                starts.append(pc)
                if node.label_name is not None:
                    if node.label_name in labels:
                        raise ValueError(
                            f"Error on line {self.helper.format_line_ref(node.source_line)} "
                            f"('{node.source_line.text}'): Duplicate label definition: {node.label_name}"
                        )
                    labels[node.label_name] = pc

                if minimum:
                    size = node.estimate_min_size(self.helper, pc, guess, constants)
                else:
                    size = node.estimate_current_size(self.helper, pc, guess, constants)
                sizes.append(size)
                pc += size

            if labels == guess:
                return LayoutState(labels=labels, starts=starts, sizes=sizes)
            guess = labels

        mode = "minimum" if minimum else "current"
        raise ValueError(f"{mode.title()} layout stabilization failed after 32 passes")
