from enum import StrEnum, auto

from dataclasses import dataclass
from VariableManager import VarTypes, Variable, ByteVariable, VarManager
from StackManager import StackManager
from RegisterManager import RegisterManager, RegisterMode
from ConditionHelper import IfElseClause
import re
from re import Match

class CommandTypes(StrEnum):
    ASSIGN = auto()
    IF = auto()
    VARDEF = auto()
    VARDEFWV = auto()

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
    
class VarDefCommand(Command):
    REGEX = r'(\w+)\s+(\w+)\s*=\s*(\w+)'
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
    REGEX = r'(\w+)\s+(\w+)$'
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
          
class Compiler:
    def __init__(self, comment_char:str, variable_start_addr:int = 0x0000, 
                 variable_end_addr:int = 0x0100, 
                 stack_start_addr:int=0x0100, 
                 stack_size:int = 256,
                 memory_size:int = 65536):
        
        if stack_size != 256:
            raise ValueError("Stack size must be 256 bytes.")
        
        self.comment_char = comment_char
        self.var_manager = VarManager(variable_start_addr, variable_end_addr, memory_size)
        self.register_manager = RegisterManager()
        self.stack_manager = StackManager(stack_start_addr, memory_size)
        self.lines:list[str] = []

    def load_lines(self, filename:str) -> None:
        with open(filename, 'r') as file:
            self.lines = file.readlines()
    
    def break_commands(self) -> None:
        self.lines = [line.split(';')[0].strip() for line in self.lines if line.strip() and not line.startswith(self.comment_char)]

    def clean_lines(self) -> None:
        self.lines = [re.sub(r'\s+', ' ', line).strip() for line in self.lines if line.strip() and not line.startswith(self.comment_char)]
    
    def compile_lines(self):
        pre_assembly_lines:list[str] = []
        if self.grouped_lines is None:
            raise ValueError("Commands must be grouped before compilation.")
         
        for command in self.grouped_lines:
            if type(command) is VarDefCommand:                
                new_lines = self.__create_var_with_value(command)
                pre_assembly_lines.extend(new_lines)
            elif type(command) is VarDefCommandWithoutValue:
                self.__create_var(command)
            elif type(command) is AssignCommand:
                new_lines = self.__assign_variable(command)
                pre_assembly_lines.extend(new_lines)
            else:
                raise ValueError(f"Unsupported command type: {command.command_type}")
        self.pre_assembly_lines = pre_assembly_lines


    def __create_var_with_value(self, command:VarDefCommand) -> list[str]:
        pre_assembly_lines = []
        new_var = self.var_manager.create_variable(
                    var_name=command.var_name, 
                    var_type=command.var_type, 
                    var_value=command.var_value)
        
        if command.var_type == VarTypes.BYTE:
            pre_assembly_lines.append(f"ldi #{new_var.address}")
            pre_assembly_lines.append("mov marl, ra")
            pre_assembly_lines.append(f"ldi #{command.var_value}")
            pre_assembly_lines.append("strl ra")

            self.register_manager.ra.set_variable(new_var, RegisterMode.VALUE)
            self.register_manager.marl.set_variable(new_var, RegisterMode.ADDR)

        else:
            raise ValueError(f"Unsupported variable type: {command.var_type}")
        
        return pre_assembly_lines
    
    def __create_var(self, command:VarDefCommandWithoutValue)-> list[str]:
        pre_assembly_lines = []
        new_var:Variable = self.var_manager.create_variable(var_name=command.var_name, var_type=command.var_type, var_value=0)
        
        return pre_assembly_lines
    
    def __set_marl(self, var:Variable) -> list[str]:
        pre_assembly_lines = []
        marl = self.register_manager.marl
        ra = self.register_manager.ra

        if marl.variable == var and marl.mode == RegisterMode.ADDR:
            return pre_assembly_lines
        
        if (ra.variable == var and ra.mode == RegisterMode.ADDR):
            pre_assembly_lines.append("mov marl, ra")
            marl.set_variable(var, RegisterMode.ADDR)
            return pre_assembly_lines
        
        pre_assembly_lines.append(f"ldi #{var.address}")
        pre_assembly_lines.append("mov marl, ra")
        marl.set_variable(var, RegisterMode.ADDR)
        ra.set_variable(var, RegisterMode.ADDR)

        return pre_assembly_lines

    def __assign_variable(self, command:AssignCommand) -> list[str]:
        pre_assembly_lines = []
        var:Variable = self.var_manager.get_variable(command.var_name)
        
        if var is None:
            raise ValueError(f"Cannot assign to undefined variable: {command.var_name}")
        
        if type(var) == VarTypes.BYTE.value:
            
            set_mar_lines = self.__set_marl(var)
            pre_assembly_lines.extend(set_mar_lines)
            ra = self.register_manager.ra
            if command.new_value.isdigit():
                reg_with_const = self.register_manager.check_for_const(int(command.new_value))
                if reg_with_const is not None:
                    pre_assembly_lines.append(f"strl {reg_with_const.name}")
                    return pre_assembly_lines
                
                pre_assembly_lines.append(f"ldi #{command.new_value}")
                pre_assembly_lines.append("strl ra")
                ra.set_mode(RegisterMode.CONST, int(command.new_value))
                return pre_assembly_lines
            elif self.var_manager.check_variable_exists(command.new_value):
                var_to_assign:Variable = self.var_manager.get_variable(command.new_value)
                raise NotImplementedError("Assignment from variable is not implemented yet.")
            else:
                raise NotImplementedError("Assignment from non-constant or non-variable is not implemented yet.")

        else:
            raise ValueError(f"Unsupported variable type for assignment: {var.var_type}")
        
        return pre_assembly_lines
    
    @staticmethod
    def __group_line_commands(lines:list[str]) -> list[Command]:
        grouped_lines:list[Command] = []
        lindex = 0
        while lindex < len(lines):
            line = lines[lindex]
            if VarDefCommand.match_regex(line):
                print(f"'{line}' matches VarDefCommand regex")
                grouped_lines.append(VarDefCommand(line))
                lindex += 1
            elif VarDefCommandWithoutValue.match_regex(line):
                print(f"'{line}' matches VarDefCommandWithoutValue regex")
                grouped_lines.append(VarDefCommandWithoutValue(line))
                lindex += 1
            elif AssignCommand.match_regex(line):
                print(f"'{line}' matches AssignCommand regex")
                grouped_lines.append(AssignCommand(line))
                lindex += 1
            elif line.startswith('if'):
                print(f"'{line}' starts an if clause")
                group = []
                while lindex < len(lines):
                    if lines[lindex].startswith('endif'):
                        del lines[lindex]
                        break
                    group.append(lines[lindex])
                    lindex += 1
                if_clause = IfElseClause.parse_from_lines(group)
                print(if_clause)
                if_clause.apply_to_all_lines(Compiler.__group_line_commands)
                grouped_lines.append(Command(CommandTypes.IF, if_clause))
            else:
                command_type = Compiler.__determine_command_type(line)
                if command_type is None:
                    raise ValueError(f"Unknown command type for line: '{line}'")
                grouped_lines.append(Command(command_type, line))
                lindex += 1
        return grouped_lines

    def group_commands(self) -> None:
        self.grouped_lines:list[Command] = self.__group_line_commands(self.lines)

    
    @staticmethod
    def __determine_command_type(line:str) -> str:
        if re.match(r'^\w+\s*=\s*.+$', line):
            return "assign"
        return None
            


if __name__ == "__main__":
    compiler = Compiler(
        comment_char='//',
        variable_start_addr=0x0000, 
        variable_end_addr=0x0100, 
        memory_size=65536)
    
    compiler.load_lines('modules/test2.txt')
    compiler.break_commands()
    compiler.clean_lines()
    compiler.group_commands()
    compiler.compile_lines()

    print("Grouped Commands:" + str(compiler.grouped_lines))

    for i in compiler.pre_assembly_lines:
        print(i)
    

