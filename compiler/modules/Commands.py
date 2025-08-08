from enum import StrEnum, auto
from VariableManager import VarTypes, Variable, ByteVariable, VarManager
from ConditionHelper import IfElseClause, GroupObject, Condition
import re

IDENT = r'[A-Za-z_][A-Za-z0-9_]*'

class CommandTypes(StrEnum):
    ASSIGN = auto()
    CONDITION = auto()
    VARDEF = auto()
    VARDEFWV = auto()
    IF = auto()
    FREE = auto()

def types_pattern():
    # VarTypes isimlerini lower-case birleştiriyoruz
    from VariableManager import VarTypes
    return r'(?:' + '|'.join(t.name.lower() for t in VarTypes) + r')'

class Command:
    REGEX:str = ""
    TYPE:CommandTypes = None
    def __init__(self, command_type:str, line:str):
        self.command_type = command_type
        self.line = line
    
    def __repr__(self):
        return f"({self.command_type} : '{self.line}')"
    
    def parse_params(self):
        raise NotImplementedError("This method should be implemented by subclasses.")
    
    @classmethod
    def match_regex(cls, line: str) -> re.Match[str] | None:
        return re.match(cls.REGEX, line)

class FreeCommand(Command):
    REGEX = r'^free\s+(\w+)+;?$'
    TYPE = CommandTypes.FREE

    def __init__(self, line:str):
        super().__init__(CommandTypes.FREE, line)
        self.var_name:str = ""
        self.parse_params()
    
    def parse_params(self):
        match = self.match_regex(self.line)
        if match:
            self.var_name = match.group(1)
        else:
            raise ValueError(f"Invalid free command: {self.line}")
    
class VarDefCommand(Command):
    
    REGEX = rf'^\s*(?P<type>{types_pattern()})\s+(?P<name>{IDENT})\s*=\s*(?P<value>.+?)\s*;?\s*$'
    TYPE = CommandTypes.VARDEF
    def __init__(self, line:str):
        super().__init__(CommandTypes.VARDEF, line)
        self.var_name:str = ""
        self.var_type:VarTypes = VarTypes.BYTE
        self.var_value:any = None
        self.parse_params()
    
    def parse_params(self):
        match = self.match_regex(self.line)
        if match:
            self.var_name = match.group(2)
            self.var_type = VarTypes[match.group(1).upper()]
            if self.var_type == VarTypes.BYTE:
                self.var_value = int(match.group(3))
            else:
                raise ValueError(f"Unsupported variable type: {self.var_type}")
        else:
            raise ValueError(f"Invalid variable definition: {self.line}")

class VarDefCommandWithoutValue(VarDefCommand):
    REGEX = rf'^\s*(?P<type>{types_pattern()})\s+(?P<name>{IDENT})\s*;?\s*$'
    TYPE = CommandTypes.VARDEFWV
    
    def __init__(self, line:str):
        super().__init__(line)
        self.var_name:str = ""
        self.var_type:VarTypes = VarTypes.BYTE
        self.parse_params()
    
    def parse_params(self):
        match = self.match_regex(self.line)
        if match:
            self.var_name = match.group(2)
            self.var_type = VarTypes[match.group(1).upper()]
        else:
            raise ValueError(f"Invalid variable definition without value: {self.line}")

class AssignCommand(Command):
    REGEX = r'^(\w+)\s*=\s*(.+)'
    TYPE = CommandTypes.ASSIGN
    
    def __init__(self, line:str):
        super().__init__(CommandTypes.ASSIGN, line)
        self.var_name:str = ""
        self.new_value:any = None
        self.parse_params()
    
    def parse_params(self):
        match = self.match_regex(self.line)
        if match:
            self.var_name = match.group(1)
            self.new_value = match.group(2)
        else:
            raise ValueError(f"Invalid assignment command: {self.line}")


if __name__ == "__main__":
    # Example usage
    command = VarDefCommand("byte myVar = 10;")
    print(command.REGEX)
    print(command.var_name)  # Output: myVar
    print(command.var_type)  # Output: VarTypes.BYTE
    print(command.var_value)  # Output: 10

    free_command = FreeCommand("free myVar;")
    print(free_command.var_name)  # Output: myVar

    assign_command = AssignCommand("myVar = 20")
    print(assign_command.var_name)  # Output: myVar
    print(assign_command.new_value)  # Output: 20