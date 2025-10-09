from enum import StrEnum, auto
import re
import logging

from VariableManager import VarTypes
from ConditionHelper import DirectAssemblyClause
import CompilerStaticMethods as CSM

logger = logging.getLogger(__name__)

VARIABLE_IDENT = r'[A-Za-z_][A-Za-z0-9_]*'
NUMBER_LITERAL = r'(0x|0b|)[A-Za-z0-9_]*'


class CommandTypes(StrEnum):
    """Command type enumeration"""
    ASSIGN = auto()
    CONDITION = auto()
    VARDEF = auto()
    VARDEFWV = auto()
    IF = auto()
    WHILE = auto()
    FREE = auto()
    DIRECT_ASSEMBLY = auto()
    STORE_DIRECT_ADDRESS = auto()


def types_pattern():
    """Generate regex pattern for variable types"""
    return r'(?:' + '|'.join(t.name.lower() for t in VarTypes) + r')'


class Command:
    """Base command class"""
    REGEX: str = ""
    TYPE: CommandTypes = None
    
    def __init__(self, command_type: str, line: str):
        self.command_type = command_type
        self.line = line
    
    def __repr__(self):
        return f"({self.command_type}: '{self.line}')"
    
    def parse_params(self):
        raise NotImplementedError("This method should be implemented by subclasses.")
    
    @classmethod
    def match_regex(cls, line: str) -> re.Match[str] | None:
        return re.match(cls.REGEX, line, re.VERBOSE)

class FreeCommand(Command):
    """Free/deallocate variable command"""
    REGEX = r'^free\s+(\w+)+;?$'
    TYPE = CommandTypes.FREE

    def __init__(self, line: str):
        super().__init__(CommandTypes.FREE, line)
        self.var_name: str = ""
        self.parse_params()
    
    def parse_params(self):
        match = self.match_regex(self.line)
        if match:
            self.var_name = match.group(1)
        else:
            raise ValueError(f"Invalid free command: {self.line}")


class DirectAssemblyCommand(Command):
    """Direct assembly insertion command"""
    TYPE = CommandTypes.DIRECT_ASSEMBLY
    
    def __init__(self, dasm_clause: DirectAssemblyClause):
        super().__init__(CommandTypes.DIRECT_ASSEMBLY, dasm_clause)
        self.assembly_lines: list[str] = dasm_clause.lines
        self.parse_params()
    
    def parse_params(self):
        pass


class VarDefCommand(Command): 
    """Variable definition with initialization"""
    REGEX = rf"""^\s*(?:(?P<volatile1>(?i:volatile))\s+)? (?P<type>{types_pattern()})\s*(?:\[(?P<size>\d*)\])?(?:\s+(?P<volatile2>(?i:volatile)))? \s+(?P<name>{VARIABLE_IDENT})\s*=\s*(?P<value>.+?)\s*;?\s*$"""
    TYPE = CommandTypes.VARDEF

    def __init__(self, line: str):
        super().__init__(CommandTypes.VARDEF, line)
        self.var_name: str = ""
        self.var_type: VarTypes = VarTypes.BYTE
        self.var_value: any = None
        self.array_length: int | None = None
        self.parse_params()
    
    def parse_params(self):
        match = re.match(self.REGEX, self.line, re.VERBOSE)
        if not match:
            raise ValueError(f"Invalid variable definition: {self.line}")

        self.is_volatile = bool(match.group('volatile1') or match.group('volatile2'))

        base_type = match.group('type').upper()
        size_text = match.group('size')
        name = match.group('name')
        value = match.group('value')

        if size_text is not None:
            if not hasattr(VarTypes, 'BYTE_ARRAY'):
                raise ValueError("VarTypes.BYTE_ARRAY not defined.")
            self.var_type = VarTypes.BYTE_ARRAY
            self.array_length = int(size_text) if size_text != '' else None
        else:
            self.var_type = VarTypes[base_type]

        self.var_name = name
        logger.debug(f"Variable definition: '{self.var_name}' volatile={self.is_volatile} type={self.var_type} initial_value='{value}'")
        if self.var_type in (VarTypes.BYTE, VarTypes.UINT16):
            try:
                self.var_value = CSM.convert_to_decimal(value)
            except ValueError:
                raise ValueError(f"Unsupported initial value for scalar: {value}")
        elif self.var_type == VarTypes.BYTE_ARRAY:
            raise NotImplementedError("Array initialization not yet supported.")
        else:
            raise ValueError(f"Unsupported variable type: {self.var_type}")
    


class VarDefCommandWithoutValue(VarDefCommand):
    """Variable definition without initialization"""
    REGEX = rf'''^\s*(?P<type>{types_pattern()})\s*(?:\[(?P<size>\d*)\])?\s+(?P<name>{VARIABLE_IDENT})\s*;?\s*$'''
    TYPE = CommandTypes.VARDEFWV
    
    def __init__(self, line: str):
        Command.__init__(self, CommandTypes.VARDEFWV, line)
        self.var_name: str = ""
        self.var_type: VarTypes = VarTypes.BYTE
        self.array_length: int | None = None
        self.parse_params()
    
    def parse_params(self):
        match = re.match(self.REGEX, self.line, re.VERBOSE)
        if not match:
            raise ValueError(f"Invalid variable definition without value: {self.line}")

        base_type = match.group('type').upper()
        size_text = match.group('size')
        name = match.group('name')

        if size_text is not None:
            if not hasattr(VarTypes, 'BYTE_ARRAY'):
                raise ValueError("VarTypes.BYTE_ARRAY not defined.")
            self.var_type = VarTypes.BYTE_ARRAY
            self.array_length = int(size_text) if size_text != '' else None
            if self.array_length is None:
                raise ValueError("Array length must be specified.")
        else:
            self.var_type = VarTypes[base_type]

        self.var_name = name

class AssignCommand(Command):
    # Supports: a = 5;  arr[1] = 5;  (pointer forms reserved for future)
    # Keep a broad REGEX so group_commands can detect as assignment
    REGEX = rf'^\s*(?:{VARIABLE_IDENT})(?:\s*\[[^\]]+\])?\s*=\s*.+'
    REGEX_VAR = rf'^\s*(?P<name>{VARIABLE_IDENT})\s*=\s*(?P<rhs>.+)'
    REGEX_ARRAY = rf'^\s*(?P<name>{VARIABLE_IDENT})\s*\[\s*(?P<index>[^\]]+)\s*\]\s*=\s*(?P<rhs>.+)'
    
    TYPE = CommandTypes.ASSIGN
    
    def __init__(self, line:str):
        super().__init__(CommandTypes.ASSIGN, line)
        self.var_name:str = ""
        self.new_value:any = None
        # extras
        self.is_array: bool = False
        self.index_expr: str | None = None
        self.is_deref: bool = False  # reserved for future: *ptr = ...
        self.parse_params()
    
    def parse_params(self):
        m_arr = re.match(self.REGEX_ARRAY, self.line)
        if m_arr:
            self.var_name = m_arr.group('name')
            self.index_expr = m_arr.group('index').strip()
            self.new_value = m_arr.group('rhs').strip()
            self.is_array = True
            return
        
        m_var = re.match(self.REGEX_VAR, self.line)
        if m_var:
            self.var_name = m_var.group('name').strip()
            self.new_value = m_var.group('rhs').strip()
            self.is_array = False
            return
        
        raise ValueError(f"Invalid assignment command: {self.line}")

class StoreToDirectAddressCommand(Command):
    REGEX = r'^\s*\*\s*(?P<addr>(?:0x[0-9A-Fa-f_]+|0b[01_]+|\d+))\s*=\s*(?P<rhs>.+?)\s*;?\s*$'
    TYPE = CommandTypes.STORE_DIRECT_ADDRESS

    def __init__(self, line: str):
        super().__init__(CommandTypes.STORE_DIRECT_ADDRESS, line)
        self.addr: int|None = None
        self.new_value: any = None
        self.parse_params()

    def parse_params(self):
        m = re.match(self.REGEX, self.line)
        if not m:
            raise ValueError(f"Invalid store direct address command: {self.line}")
        addr_str = m.group('addr').strip()
        self.addr = CSM.convert_to_decimal(addr_str)
        self.new_value = m.group('rhs').strip()


class WhileCommand(Command):
    REGEX = r'^while\s+(.+)$'
    TYPE = CommandTypes.WHILE

    def __init__(self, line: str):
        super().__init__(CommandTypes.WHILE, line)
        self.condition_str: str = ''
        self.parse_params()

    def parse_params(self):
        m = re.match(self.REGEX, self.line)
        if not m:
            raise ValueError(f"Invalid while command: {self.line}")
        self.condition_str = m.group(1).strip()


if __name__ == "__main__":
    # Example usage
    command = VarDefCommand("byte zero = 0")
    print(command, VarDefCommand.match_regex("byte zero = 0"))
