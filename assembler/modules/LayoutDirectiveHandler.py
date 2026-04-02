from __future__ import annotations

from typing import Dict, List, Optional, TYPE_CHECKING


if TYPE_CHECKING:
    from .AssemblyHelper import AssemblyHelper, ParsedLine


class LayoutDirectiveHandler:
    """Handle layout and padding directives such as .org, .align, and .fill."""

    def __init__(self, helper: "AssemblyHelper") -> None:
        self.helper = helper

    def estimate_size(
        self,
        instruction: str,
        args: List[str],
        current_pc: int,
        labels: Dict[str, int],
        constants: Dict[str, int],
    ) -> Optional[int]:
        instruction = instruction.upper()

        if instruction == ".FILL":
            count, _ = self.parse_fill_args(args, labels, constants)
            return count

        if instruction == ".ORG":
            target, _ = self.parse_layout_target(args, labels, constants, ".org")
            if target < current_pc:
                raise ValueError(f".org target 0x{target:04X} is behind current address 0x{current_pc:04X}")
            return target - current_pc

        if instruction == ".ALIGN":
            boundary, _ = self.parse_layout_target(args, labels, constants, ".align")
            if boundary <= 0:
                raise ValueError(".align boundary must be greater than zero")
            remainder = current_pc % boundary
            return 0 if remainder == 0 else boundary - remainder

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
        instruction = instruction.upper()

        if instruction == ".FILL":
            count, fill_byte = self.parse_fill_args(args, labels, constants)
            return [f"{fill_byte:08b}" for _ in range(count)]

        if instruction == ".ORG":
            target, fill_byte = self.parse_layout_target(args, labels, constants, ".org")
            if target < current_pc:
                raise ValueError(f".org target 0x{target:04X} is behind current address 0x{current_pc:04X}")
            return [f"{fill_byte:08b}" for _ in range(target - current_pc)]

        if instruction == ".ALIGN":
            boundary, fill_byte = self.parse_layout_target(args, labels, constants, ".align")
            if boundary <= 0:
                raise ValueError(".align boundary must be greater than zero")
            remainder = current_pc % boundary
            padding = 0 if remainder == 0 else boundary - remainder
            return [f"{fill_byte:08b}" for _ in range(padding)]

        return None

    def parse_fill_args(
        self,
        args: List[str],
        labels: Dict[str, int],
        constants: Dict[str, int],
    ) -> tuple[int, int]:
        if len(args) not in {1, 2}:
            raise ValueError(".fill requires count and optional fill byte")

        count = self.resolve_non_negative(args[0], labels, constants, ".fill")
        fill_byte = 0 if len(args) == 1 else self.resolve_byte(args[1], labels, constants, ".fill")
        return count, fill_byte

    def parse_layout_target(
        self,
        args: List[str],
        labels: Dict[str, int],
        constants: Dict[str, int],
        directive: str,
    ) -> tuple[int, int]:
        if len(args) not in {1, 2}:
            raise ValueError(f"{directive} requires target and optional fill byte")
        target = self.resolve_non_negative(args[0], labels, constants, directive)
        fill_byte = 0 if len(args) == 1 else self.resolve_byte(args[1], labels, constants, directive)
        return target, fill_byte

    def resolve_non_negative(
        self,
        token: str,
        labels: Dict[str, int],
        constants: Dict[str, int],
        directive: str,
    ) -> int:
        resolved = self.helper.resolve_value(token, labels, constants)
        if resolved.value is None:
            raise ValueError(f"{directive} could not resolve operand {token}")
        if resolved.value < 0:
            raise ValueError(f"{directive} value must be non-negative, got {resolved.value}")
        return resolved.value

    def resolve_byte(
        self,
        token: str,
        labels: Dict[str, int],
        constants: Dict[str, int],
        directive: str,
    ) -> int:
        resolved = self.helper.resolve_value(token, labels, constants)
        if resolved.value is None:
            raise ValueError(f"{directive} could not resolve operand {token}")
        if not (0 <= resolved.value <= 0xFF):
            raise ValueError(f"{directive} fill byte {resolved.value} out of range (0-255)")
        return resolved.value
