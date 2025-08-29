from __future__ import annotations
from typing import Protocol, Dict, Any

class Device(Protocol):
    id: str
    name: str
    def read(self, addr: int) -> int: ...
    def write(self, addr: int, value: int) -> None: ...
    def tick(self, cycles: int = 1) -> None: ...
    def reset(self) -> None: ...
    def info(self) -> Dict[str, Any]: ...

class MmioDevice:
    def __init__(self, id: str, name: str, base: int, size: int):
        self.id = id
        self.name = name
        self.base = base & 0xFFFF
        self.size = size & 0xFFFF

    def in_range(self, addr: int) -> bool:
        addr &= 0xFFFF
        return self.base <= addr < (self.base + self.size)

    def read(self, addr: int) -> int:
        return 0

    def write(self, addr: int, value: int) -> None:
        pass

    def tick(self, cycles: int = 1) -> None:
        pass

    def reset(self) -> None:
        pass

    def info(self) -> Dict[str, Any]:
        return {"id": self.id, "name": self.name, "base": self.base, "size": self.size}
