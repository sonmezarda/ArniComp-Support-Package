from __future__ import annotations

import os
import re
from typing import Callable, Dict, List, Optional, Sequence, Tuple


class FunctionImportResolver:
    """Resolve selected function imports from library files and append them after main source."""

    def __init__(
        self,
        comment_char: str,
        constant_keyword: str,
        source_line_factory: Callable[[int, str, str], object],
        preprocessor_expand: Callable[[List[str], str], List[object]],
    ) -> None:
        self.comment_char = comment_char
        self.constant_keyword = constant_keyword.lower()
        self.source_line_factory = source_line_factory
        self.preprocessor_expand = preprocessor_expand
        self.import_keyword = ".import"
        self.export_keyword = ".export"
        self.func_keyword = ".func"
        self.endfunc_keyword = ".endfunc"

    def strip_comments(self, text: str) -> str:
        return text.strip()

    def split_label_prefix(self, text: str) -> Tuple[Optional[str], str]:
        match = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\:(.*)$", text)
        if not match:
            return None, text.strip()
        return match.group(1).upper(), match.group(2).strip()

    def parse_import(self, text: str) -> Optional[Tuple[str, List[str]]]:
        stripped = self.strip_comments(text)
        if not stripped:
            return None

        match = re.match(r"^\.import\s+(?P<quote>['\"])(?P<path>.+?)(?P=quote)\s+(?P<symbols>.+)$", stripped, re.IGNORECASE)
        if not match:
            return None

        raw_symbols = [part.strip() for part in match.group("symbols").split(",")]
        symbols = [symbol.upper() for symbol in raw_symbols if symbol]
        if not symbols:
            raise ValueError(".import requires at least one symbol")
        for symbol in symbols:
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", symbol):
                raise ValueError(f"Invalid imported symbol name: {symbol}")
        return match.group("path"), symbols

    def parse_export(self, text: str) -> Optional[str]:
        stripped = self.strip_comments(text)
        if not stripped:
            return None

        parts = stripped.split(None, 1)
        if len(parts) != 2 or parts[0].lower() != self.export_keyword:
            return None

        symbol = parts[1].strip().upper()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", symbol):
            raise ValueError(f"Invalid exported symbol name: {parts[1].strip()}")
        return symbol

    def is_func_start(self, text: str) -> bool:
        return self.strip_comments(text).lower() == self.func_keyword

    def is_func_end(self, text: str) -> bool:
        return self.strip_comments(text).lower() == self.endfunc_keyword

    def is_constant_line(self, text: str) -> bool:
        stripped = self.strip_comments(text)
        if not stripped:
            return False
        parts = stripped.split(None, 1)
        return bool(parts and parts[0].lower() == self.constant_keyword)

    def extract_library_sections(
        self,
        lines: Sequence[object],
        library_source: str,
    ) -> Tuple[List[object], Dict[str, List[object]], Dict[str, bool]]:
        prelude_lines: List[object] = []
        function_blocks: Dict[str, List[object]] = {}
        exported_symbols: Dict[str, bool] = {}

        inside_func = False
        current_block: List[object] = []
        current_name: Optional[str] = None

        for source_line in lines:
            text = source_line.text

            try:
                exported = self.parse_export(text)
            except ValueError as exc:
                raise ValueError(f"Error in {library_source}:{source_line.line_number} ('{text}'): {exc}") from exc

            if exported is not None:
                exported_symbols[exported] = True
                continue

            if self.is_func_start(text):
                if inside_func:
                    raise ValueError(
                        f"Error in {library_source}:{source_line.line_number} ('{text}'): nested .func blocks are not allowed"
                    )
                inside_func = True
                current_block = []
                current_name = None
                continue

            if self.is_func_end(text):
                if not inside_func:
                    raise ValueError(
                        f"Error in {library_source}:{source_line.line_number} ('{text}'): unexpected .endfunc"
                    )
                if current_name is None:
                    raise ValueError(
                        f"Error in {library_source}:{source_line.line_number} ('{text}'): .func block must start with a label"
                    )
                function_blocks[current_name] = list(current_block)
                inside_func = False
                current_block = []
                current_name = None
                continue

            if inside_func:
                if current_name is None:
                    label_name, _ = self.split_label_prefix(text)
                    if label_name is None:
                        raise ValueError(
                            f"Error in {library_source}:{source_line.line_number} ('{text}'): first line after .func must be a label"
                        )
                    current_name = label_name
                current_block.append(source_line)
                continue

            if self.is_constant_line(text):
                prelude_lines.append(source_line)

        if inside_func:
            raise ValueError(f"Error in {library_source}: missing .endfunc for .func block")

        return prelude_lines, function_blocks, exported_symbols

    def resolve_imports(self, expanded_lines: List[object]) -> List[object]:
        main_lines: List[object] = []
        appended_lines: List[object] = []
        appended_keys = set()
        imported_functions = set()

        for source_line in expanded_lines:
            try:
                import_result = self.parse_import(source_line.text)
            except ValueError as exc:
                raise ValueError(f"Error on line {source_line.source_name}:{source_line.line_number} ('{source_line.text}'): {exc}") from exc

            if import_result is None:
                main_lines.append(source_line)
                continue

            import_target, requested_symbols = import_result
            base_dir = os.path.dirname(os.path.abspath(source_line.source_name)) if source_line.source_name != "<input>" else os.getcwd()
            import_path = import_target
            if not os.path.isabs(import_path):
                import_path = os.path.abspath(os.path.join(base_dir, import_target))

            if not os.path.exists(import_path):
                raise ValueError(
                    f"Error on line {source_line.source_name}:{source_line.line_number} ('{source_line.text}'): "
                    f"Imported file not found: {import_target}"
                )

            try:
                with open(import_path, "r", encoding="utf-8") as f:
                    imported_raw_lines = f.readlines()
            except OSError as exc:
                raise ValueError(
                    f"Error on line {source_line.source_name}:{source_line.line_number} ('{source_line.text}'): "
                    f"Could not read imported file: {import_target}"
                ) from exc

            imported_expanded = self.preprocessor_expand(imported_raw_lines, import_path)
            prelude_lines, function_blocks, exported_symbols = self.extract_library_sections(imported_expanded, import_path)

            for symbol in requested_symbols:
                if symbol not in exported_symbols:
                    raise ValueError(
                        f"Error on line {source_line.source_name}:{source_line.line_number} ('{source_line.text}'): "
                        f"Imported symbol '{symbol}' is not exported by {import_target}"
                    )
                if symbol not in function_blocks:
                    raise ValueError(
                        f"Error on line {source_line.source_name}:{source_line.line_number} ('{source_line.text}'): "
                        f"Exported symbol '{symbol}' has no matching .func block in {import_target}"
                    )

            for extra_line in prelude_lines:
                key = (extra_line.source_name, extra_line.line_number, extra_line.text)
                if key not in appended_keys:
                    appended_keys.add(key)
                    appended_lines.append(extra_line)

            for symbol in requested_symbols:
                func_key = (import_path, symbol)
                if func_key in imported_functions:
                    continue
                imported_functions.add(func_key)
                for extra_line in function_blocks[symbol]:
                    key = (extra_line.source_name, extra_line.line_number, extra_line.text)
                    if key not in appended_keys:
                        appended_keys.add(key)
                        appended_lines.append(extra_line)

        return [*main_lines, *appended_lines]
