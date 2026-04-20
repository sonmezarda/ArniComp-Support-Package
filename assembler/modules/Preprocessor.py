from __future__ import annotations

import os
import re
from typing import Callable, Dict, List, Optional, Tuple

from .CommentStripper import CommentStripper


class Preprocessor:
    """Expand source-level constructs such as includes and repeat blocks."""

    def __init__(
        self,
        comment_char: str,
        block_comment_start: str,
        block_comment_end: str,
        source_line_factory: Callable[[int, str, str], object],
        expression_evaluator: Callable[[str, Optional[Dict[str, int]]], int],
    ) -> None:
        self.comment_char = comment_char
        self.block_comment_start = block_comment_start
        self.block_comment_end = block_comment_end
        self.source_line_factory = source_line_factory
        self.expression_evaluator = expression_evaluator
        self.include_keyword = ".include"
        self.repeat_keyword = ".repeat"
        self.define_keyword = ".define"
        self.if_keyword = ".if"
        self.else_keyword = ".else"
        self.endif_keyword = ".endif"

    def strip_comments_from_lines(self, lines: List[str], source_name: str) -> List[str]:
        stripper = CommentStripper(
            line_comment=self.comment_char,
            block_comment_start=self.block_comment_start,
            block_comment_end=self.block_comment_end,
        )
        return stripper.strip_lines(lines, source_name=source_name)

    def parse_include_target(self, text: str) -> Optional[str]:
        stripped = text.strip()
        if not stripped:
            return None

        parts = stripped.split(None, 1)
        if len(parts) != 2 or parts[0].lower() != self.include_keyword:
            return None

        target = parts[1].strip()
        if len(target) < 2 or target[0] not in {'"', "'"} or target[-1] != target[0]:
            raise ValueError("Include path must be wrapped in quotes")
        return target[1:-1]

    def parse_repeat_count(self, text: str, defines: Dict[str, int]) -> Optional[int]:
        stripped = text.strip()
        if not stripped:
            return None

        parts = stripped.split(None, 1)
        if len(parts) != 2 or parts[0].lower() != self.repeat_keyword:
            return None

        if not parts[1].endswith("{"):
            raise ValueError(".repeat syntax must end with '{'")

        expr = parts[1][:-1].strip()
        if not expr:
            raise ValueError(".repeat requires a repeat count expression")

        count = self.expression_evaluator(expr, defines)
        if count < 0:
            raise ValueError(".repeat count must be non-negative")
        return count

    def parse_define(self, text: str) -> Optional[Tuple[str, str]]:
        stripped = text.strip()
        if not stripped:
            return None

        parts = stripped.split(None, 2)
        if len(parts) < 3 or parts[0].lower() != self.define_keyword:
            return None

        name = parts[1].strip().upper()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            raise ValueError(f"Invalid .define name: {parts[1]}")
        return name, parts[2].strip()

    def parse_if_condition(self, text: str) -> Optional[str]:
        stripped = text.strip()
        if not stripped:
            return None

        parts = stripped.split(None, 1)
        if len(parts) != 2 or parts[0].lower() != self.if_keyword:
            return None
        return parts[1].strip()

    def expand(
        self,
        raw_lines: List[str],
        source_name: str = "<input>",
        include_stack: Optional[Tuple[str, ...]] = None,
        defines: Optional[Dict[str, int]] = None,
    ) -> List[object]:
        include_stack = include_stack or tuple()
        defines = defines if defines is not None else {}
        normalized_source = os.path.abspath(source_name) if source_name != "<input>" else source_name
        sanitized_lines = self.strip_comments_from_lines(raw_lines, source_name)

        if normalized_source in include_stack:
            chain = " -> ".join([*include_stack, normalized_source])
            raise ValueError(f"Recursive include detected: {chain}")

        base_dir = os.path.dirname(normalized_source) if normalized_source != "<input>" else os.getcwd()
        expanded: List[object] = []
        index = 0

        while index < len(raw_lines):
            raw_line = raw_lines[index].rstrip("\r\n")
            sanitized_line = sanitized_lines[index]
            line_number = index + 1
            stripped = sanitized_line

            try:
                include_target = self.parse_include_target(sanitized_line)
            except ValueError as exc:
                raise ValueError(f"Error on line {source_name}:{line_number} ('{raw_line.strip()}'): {exc}") from exc

            if include_target is not None:
                include_path = include_target
                if not os.path.isabs(include_path):
                    include_path = os.path.abspath(os.path.join(base_dir, include_target))

                if not os.path.exists(include_path):
                    raise ValueError(
                        f"Error on line {source_name}:{line_number} ('{raw_line.strip()}'): "
                        f"Included file not found: {include_target}"
                    )

                try:
                    with open(include_path, "r", encoding="utf-8") as f:
                        included_raw_lines = f.readlines()
                except OSError as exc:
                    raise ValueError(
                        f"Error on line {source_name}:{line_number} ('{raw_line.strip()}'): "
                        f"Could not read include file: {include_target}"
                    ) from exc

                expanded.extend(
                    self.expand(
                        included_raw_lines,
                        source_name=include_path,
                        include_stack=(*include_stack, normalized_source),
                        defines=defines,
                    )
                )
                index += 1
                continue

            try:
                define_result = self.parse_define(sanitized_line)
            except ValueError as exc:
                raise ValueError(f"Error on line {source_name}:{line_number} ('{raw_line.strip()}'): {exc}") from exc

            if define_result is not None:
                name, expr = define_result
                try:
                    defines[name] = self.expression_evaluator(expr, defines)
                except ValueError as exc:
                    raise ValueError(f"Error on line {source_name}:{line_number} ('{raw_line.strip()}'): {exc}") from exc
                index += 1
                continue

            try:
                if_expr = self.parse_if_condition(sanitized_line)
            except ValueError as exc:
                raise ValueError(f"Error on line {source_name}:{line_number} ('{raw_line.strip()}'): {exc}") from exc

            if if_expr is not None:
                true_lines, false_lines, next_index = self.collect_if_blocks(
                    raw_lines,
                    sanitized_lines,
                    index + 1,
                    source_name,
                )
                try:
                    condition_value = self.expression_evaluator(if_expr, defines)
                except ValueError as exc:
                    raise ValueError(f"Error on line {source_name}:{line_number} ('{raw_line.strip()}'): {exc}") from exc
                selected = true_lines if condition_value else false_lines
                expanded.extend(
                    self.expand(
                        selected,
                        source_name=source_name,
                        include_stack=include_stack,
                        defines=defines,
                    )
                )
                index = next_index
                continue

            if stripped == self.else_keyword:
                raise ValueError(f"Error on line {source_name}:{line_number} ('{raw_line.strip()}'): unexpected .else")

            if stripped == self.endif_keyword:
                raise ValueError(f"Error on line {source_name}:{line_number} ('{raw_line.strip()}'): unexpected .endif")

            try:
                repeat_count = self.parse_repeat_count(sanitized_line, defines)
            except ValueError as exc:
                raise ValueError(f"Error on line {source_name}:{line_number} ('{raw_line.strip()}'): {exc}") from exc

            if repeat_count is not None:
                block_lines, next_index = self.collect_repeat_block(raw_lines, sanitized_lines, index + 1, source_name, defines)
                expanded_block = self.expand(
                    block_lines,
                    source_name=source_name,
                    include_stack=include_stack,
                    defines=defines,
                )
                for _ in range(repeat_count):
                    expanded.extend(expanded_block)
                index = next_index
                continue

            expanded.append(self.source_line_factory(line_number, sanitized_line, source_name))
            index += 1

        return expanded

    def collect_repeat_block(
        self,
        raw_lines: List[str],
        sanitized_lines: List[str],
        start_index: int,
        source_name: str,
        defines: Dict[str, int],
    ) -> Tuple[List[str], int]:
        block_lines: List[str] = []
        depth = 1
        index = start_index

        while index < len(raw_lines):
            raw_line = raw_lines[index].rstrip("\r\n")
            stripped = sanitized_lines[index]

            repeat_count = None
            if stripped:
                try:
                    repeat_count = self.parse_repeat_count(stripped, defines)
                except ValueError as exc:
                    raise ValueError(f"Error on line {source_name}:{index + 1} ('{raw_line.strip()}'): {exc}") from exc

            if repeat_count is not None:
                depth += 1
                block_lines.append(stripped)
                index += 1
                continue

            if stripped == "}":
                depth -= 1
                if depth == 0:
                    return block_lines, index + 1
                block_lines.append(stripped)
                index += 1
                continue

            block_lines.append(stripped)
            index += 1

        raise ValueError(f"Error in {source_name}: missing closing '}}' for .repeat block")

    def collect_if_blocks(
        self,
        raw_lines: List[str],
        sanitized_lines: List[str],
        start_index: int,
        source_name: str,
    ) -> Tuple[List[str], List[str], int]:
        true_lines: List[str] = []
        false_lines: List[str] = []
        active = true_lines
        depth = 1
        index = start_index

        while index < len(raw_lines):
            stripped = sanitized_lines[index]

            if stripped:
                if self.parse_if_condition(stripped) is not None:
                    depth += 1
                    active.append(stripped)
                    index += 1
                    continue

                if stripped == self.else_keyword:
                    if depth == 1:
                        active = false_lines
                        index += 1
                        continue
                    active.append(stripped)
                    index += 1
                    continue

                if stripped == self.endif_keyword:
                    depth -= 1
                    if depth == 0:
                        return true_lines, false_lines, index + 1
                    active.append(stripped)
                    index += 1
                    continue

            active.append(stripped)
            index += 1

        raise ValueError(f"Error in {source_name}: missing closing '.endif' for .if block")
