from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class BaseTag:
    kind: str


@dataclass(frozen=True)
class AbsAddrTag(BaseTag):
    addr: int

    def __init__(self, addr: int):
        object.__setattr__(self, 'kind', 'abs')
        object.__setattr__(self, 'addr', addr & 0xFFFF)


@dataclass(frozen=True)
class SymbolBaseTag(BaseTag):
    region_id: str  # typically variable name for now

    def __init__(self, region_id: str):
        object.__setattr__(self, 'kind', 'symbase')
        object.__setattr__(self, 'region_id', region_id)


@dataclass(frozen=True)
class ElementTag(BaseTag):
    region_id: str
    elem_size: int
    offset: int  # in bytes, const index * elem_size

    def __init__(self, region_id: str, elem_size: int, offset: int):
        object.__setattr__(self, 'kind', 'element')
        object.__setattr__(self, 'region_id', region_id)
        object.__setattr__(self, 'elem_size', int(elem_size))
        object.__setattr__(self, 'offset', int(offset))


@dataclass(frozen=True)
class ExprAddrTag(BaseTag):
    region_id: str
    elem_size: int
    index_reg: Optional[str]
    const_offset: int = 0

    def __init__(self, region_id: str, elem_size: int, index_reg: Optional[str], const_offset: int = 0):
        object.__setattr__(self, 'kind', 'expr')
        object.__setattr__(self, 'region_id', region_id)
        object.__setattr__(self, 'elem_size', int(elem_size))
        object.__setattr__(self, 'index_reg', index_reg)
        object.__setattr__(self, 'const_offset', int(const_offset))


def tags_equal(a: Optional[BaseTag], b: Optional[BaseTag]) -> bool:
    if a is None or b is None:
        return False
    if a.kind != b.kind:
        # allow equality if both resolve to same absolute address
        if isinstance(a, AbsAddrTag) and isinstance(b, AbsAddrTag):
            return a.addr == b.addr
        return False
    return a == b
