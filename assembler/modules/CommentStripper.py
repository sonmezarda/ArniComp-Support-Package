from __future__ import annotations

from typing import Iterable, List, Optional


class CommentStripper:
    """Strip line and block comments while preserving quoted literals."""

    def __init__(
        self,
        line_comment: str = ";",
        block_comment_start: str = "/*",
        block_comment_end: str = "*/",
    ) -> None:
        self.line_comment = line_comment
        self.block_comment_start = block_comment_start
        self.block_comment_end = block_comment_end
        self.reset()

    def reset(self) -> None:
        self._in_block_comment = False
        self._block_comment_start_line: Optional[int] = None

    def strip_line(self, text: str, line_number: Optional[int] = None) -> str:
        result: List[str] = []
        index = 0
        quote_char: Optional[str] = None
        escaped = False

        while index < len(text):
            if self._in_block_comment:
                end_index = text.find(self.block_comment_end, index)
                if end_index == -1:
                    return "".join(result).strip()
                self._in_block_comment = False
                self._block_comment_start_line = None
                index = end_index + len(self.block_comment_end)
                continue

            ch = text[index]

            if quote_char is not None:
                result.append(ch)
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == quote_char:
                    quote_char = None
                index += 1
                continue

            if self.line_comment and text.startswith(self.line_comment, index):
                break

            if self.block_comment_start and text.startswith(self.block_comment_start, index):
                self._in_block_comment = True
                if self._block_comment_start_line is None:
                    self._block_comment_start_line = line_number
                index += len(self.block_comment_start)
                continue

            if ch in {"'", '"'}:
                quote_char = ch

            result.append(ch)
            index += 1

        return "".join(result).strip()

    def strip_lines(self, lines: Iterable[str], source_name: str = "<input>") -> List[str]:
        self.reset()
        stripped_lines: List[str] = []
        for line_number, line in enumerate(lines, start=1):
            stripped_lines.append(self.strip_line(line.rstrip("\r\n"), line_number=line_number))

        if self._in_block_comment:
            start_line = self._block_comment_start_line or "?"
            raise ValueError(f"Unterminated block comment starting at {source_name}:{start_line}")

        return stripped_lines
