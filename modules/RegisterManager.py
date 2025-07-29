from enum import IntEnum

from VariableManager import Variable

class RegisterMode(IntEnum):
    VALUE=0
    ADDR=1
    CONST=2
    UNKNOWN=3

class Register:
    def __init__(self, name:str, Variable:Variable=None, mode:RegisterMode = RegisterMode.VALUE, value:int = None):
        self.name = name
        self.variable = Variable
        self.mode = mode
        self.value = None
    
    def set_mode(self, mode:RegisterMode, value:int = None):
        self.mode = mode
        if mode == RegisterMode.CONST:
            self.variable = None
            if value is None:
                raise ValueError("Value must be provided in CONST mode")
            self.value = value
        else:
            self.value = None
            if value is not None:
                raise ValueError("Value cannot be set in VALUE or ADDR mode")
    
    def set_variable(self, variable:Variable, mode:RegisterMode = RegisterMode.VALUE):
        self.variable = variable
        self.mode = mode
        if variable is None:
            self.mode = RegisterMode.CONST

        if variable is not None and mode == RegisterMode.CONST:
            raise ValueError("Cannot set variable in CONST mode")
        
    
    
class RegisterManager():
    def __init__(self):
        self.ra:Register = Register("ra")
        self.rd:Register = Register("rd")
        self.acc:Register = Register("acc")
        self.marl:Register= Register("marl")
        self.marh:Register = Register("marh")
        self.prl:Register = Register("prl")
        self.prh:Register = Register("prh")


    def check_for_const(self, value:int) -> Register | None:
        for reg in [self.ra, self.rd, self.acc]:
            if reg.mode == RegisterMode.CONST and reg.value == value:
                return reg
            if reg.mode == RegisterMode.ADDR and reg.variable.address == value:
                return reg
        return None

    