from enum import IntEnum

from VariableManager import Variable

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

class TempVarMode(IntEnum):
    VAR_VAR_ADD=0
    VAR_CONST_ADD=1
    VAR_VAR_SUB=2
    VAR_CONST_SUB=3
    
class Register:
    def __init__(self, name:str, Variable:Variable=None, mode:RegisterMode = RegisterMode.VALUE, value:int = None):
        self.name = name
        self.variable = Variable
        self.mode = mode
        self.value = None
        self.special_expression = None
    
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
    
    def set_temp_var_mode(self,  expression:str):
        if not expression:
            raise ValueError("Expression cannot be empty in TEMPVAR mode")
        
        self.mode = RegisterMode.TEMPVAR
        self.special_expression = expression
        self.variable= None
        self.value = None
        
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
        

        
        
    
    
class RegisterManager():
    def __init__(self):
        self.ra:Register = Register("ra")
        self.rd:Register = Register("rd")
        self.acc:Register = Register("acc")
        self.marl:Register= Register("marl")
        self.marh:Register = Register("marh")
        self.prl:Register = Register("prl")
        self.prh:Register = Register("prh")

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

    