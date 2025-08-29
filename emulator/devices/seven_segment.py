from __future__ import annotations
from typing import Callable, Dict, Any

from .base import MmioDevice

SEG_BITS = ["a","b","c","d","e","f","g","dp"]

class SevenSegmentDevice(MmioDevice):
    def __init__(self, id: str, base: int, on_change: Callable[[Dict[str, Any]], None] | None = None):
        super().__init__(id=id, name="SevenSegment", base=base, size=1)
        self.value: int = 0
        self.on_change = on_change

    def read(self, addr: int) -> int:
        return self.value & 0xFF

    def write(self, addr: int, value: int) -> None:
        self.value = value & 0xFF
        if self.on_change:
            self.on_change(self.info())

    def reset(self) -> None:
        self.value = 0
        if self.on_change:
            self.on_change(self.info())

    def info(self) -> Dict[str, Any]:
        bits = {name: bool((self.value >> i) & 1) for i, name in enumerate(SEG_BITS)}
        return {
            **super().info(),
            "value": self.value,
            "segments": bits
        }
