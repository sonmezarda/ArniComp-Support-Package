"""
System Bus for ArniComp emulator: routes memory-mapped I/O to devices
and regular RAM accesses to internal bytearray.
"""
from __future__ import annotations
from typing import List, Optional, Dict, Any

from .devices.base import MmioDevice


class Bus:
    def __init__(self, ram_size: int = 65536):
        self.ram = bytearray(ram_size)
        self.devices: List[MmioDevice] = []

    # Device management
    def attach(self, dev: MmioDevice) -> None:
        self.devices.append(dev)

    def find_device(self, addr: int) -> Optional[MmioDevice]:
        for d in self.devices:
            if d.in_range(addr):
                return d
        return None

    # Memory operations
    def read8(self, addr: int) -> int:
        addr &= 0xFFFF
        dev = self.find_device(addr)
        if dev is not None:
            return dev.read(addr)
        return self.ram[addr]

    def write8(self, addr: int, value: int) -> None:
        addr &= 0xFFFF
        value &= 0xFF
        dev = self.find_device(addr)
        if dev is not None:
            dev.write(addr, value)
        else:
            self.ram[addr] = value

    def reset(self) -> None:
        self.ram[:] = b"\x00" * len(self.ram)
        for d in self.devices:
            d.reset()

    def devices_info(self) -> List[Dict[str, Any]]:
        return [d.info() for d in self.devices]
