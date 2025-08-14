from __future__ import annotations
from enum import IntEnum

from VariableManager import Variable
from typing import Optional
try:
    from RegTags import BaseTag, AbsAddrTag
except Exception:
    BaseTag = None  # type: ignore
    AbsAddrTag = None  # type: ignore

def is_number(self, value:str) -> bool:
        try:
            int(value)
            return True
        except ValueError:
            return False
        
class RegisterMode(IntEnum):
    VALUE=0
    ADDR=1
    CONST=2
    UNKNOWN=3
    TEMPVAR=4
    LABEL=5
    ADDR_LOW=6
    ADDR_HIGH=7

class TempVarMode(IntEnum):
    VAR_VAR_ADD=0
    VAR_CONST_ADD=1
    VAR_VAR_SUB=2
    VAR_CONST_SUB=3
    
class Register:
    def __init__(self, name:str, Variable:Variable=None, mode:RegisterMode = RegisterMode.VALUE, value:int = None, manager:'RegisterManager'=None):
        self.name = name
        self.variable = Variable
        self.mode = mode
        self.value = None
        self.special_expression = None
        self.manager = manager
        # Address/identity tag for caching (symbolic/absolute)
        self.tag = None
    
    def set_mode(self, mode:RegisterMode, value:int = None):
        self.mode = mode
        if mode == RegisterMode.CONST:
            self.variable = None
            if value is None:
                raise ValueError("Value must be provided in CONST mode")
            self.value = value
            # CONST is not an address; clear tag
            if hasattr(self, 'tag'):
                self.tag = None
        else:
            if value is not None:
                raise ValueError("Value cannot be set in VALUE or ADDR mode")
            self.value = None
        self.manager.add_changed_register(self)
    
    def set_unknown_mode(self):
        self.mode = RegisterMode.UNKNOWN
        self.variable = None
        self.value = None
        self.special_expression = None
        if hasattr(self, 'tag'):
            self.tag = None
        self.manager.add_changed_register(self)
        
    def set_label_mode(self, label_name:str):
        if not label_name:
            raise ValueError("Label name cannot be empty in LABEL mode")
        
        self.mode = RegisterMode.LABEL
        self.value = label_name
        self.variable = None
        self.special_expression = None
        if hasattr(self, 'tag'):
            self.tag = None
        self.manager.add_changed_register(self)

    def set_temp_var_mode(self,  expression:str):
        if not expression:
            raise ValueError("Expression cannot be empty in TEMPVAR mode")
        
        self.mode = RegisterMode.TEMPVAR
        self.special_expression = expression
        self.variable= None
        self.value = None
        if hasattr(self, 'tag'):
            self.tag = None
        self.manager.add_changed_register(self)
        
    def get_expression(self) -> str:
        if self.mode != RegisterMode.TEMPVAR:
            raise ValueError("Cannot get expression in non-TEMPVAR mode")
        if self.special_expression is None:
            raise ValueError("Special expression is not set")
        return self.special_expression

    def set_variable(self, variable:Variable, mode:RegisterMode = RegisterMode.VALUE):
        if variable is not None and mode == RegisterMode.CONST:
            raise ValueError("Cannot set variable in CONST mode")
        
        if variable is None:
            self.mode = RegisterMode.CONST
        self.variable = variable
        self.mode = mode     
        # If this register becomes an address holder, tag it with absolute address
        if variable is not None and mode in [RegisterMode.ADDR, RegisterMode.ADDR_LOW, RegisterMode.ADDR_HIGH]:
            try:
                if AbsAddrTag is not None:
                    self.tag = AbsAddrTag(variable.address)
            except Exception:
                pass
        else:
            if hasattr(self, 'tag'):
                self.tag = None
        self.manager.add_changed_register(self)
  
    
class RegisterManager():
    def __init__(self):
        self.ra:Register = Register("ra", manager=self)
        self.rd:Register = Register("rd", manager=self)
        self.acc:Register = Register("acc", manager=self)
        self.marl:Register= Register("marl", manager=self)
        self.marh:Register = Register("marh", manager=self)
        self.prl:Register = Register("prl", manager=self)
        self.prh:Register = Register("prh", manager=self)
        self.changed_registers:list[Register] = []

    def check_for_variable(self, variable:Variable) -> Register | None:
        for reg in [self.ra, self.rd, self.marl, self.marh]:
            if reg.mode == RegisterMode.VALUE and reg.variable == variable:
                return reg
        return None

    def check_for_const(self, value:int) -> Register | None:
        for reg in [self.ra, self.rd, self.acc]:
            if reg.mode == RegisterMode.CONST and reg.value == value:
                return reg
            if reg.mode == RegisterMode.ADDR and reg.variable.address == value:
                return reg
        return None
    
    def get_register(self, name:str) -> Register | None:
        if hasattr(self, name):
            return getattr(self, name)
        return None
    
    def reset_change_detector(self):
        self.changed_registers:list[Register] = []
    
    def add_changed_register(self, register:Register):
        if register not in self.changed_registers:
            self.changed_registers.append(register)
    
    def get_changed_registers(self) -> list[Register]:
        return self.changed_registers
    
    def set_changed_registers_as_unknown(self):
        for reg in self.changed_registers:
            reg.set_unknown_mode()
        self.reset_change_detector()

    