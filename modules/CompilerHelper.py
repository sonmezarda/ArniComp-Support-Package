from __future__ import annotations

from dataclasses import dataclass
from VariableManager import VarTypes, Variable, ByteVariable, VarManager
from StackManager import StackManager
from RegisterManager import RegisterManager, RegisterMode, Register, TempVarMode
from ConditionHelper import IfElseClause
import re

from Commands import *


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
    
    def is_variable_defined(self, var_name:str) -> bool:
        return self.var_manager.check_variable_exists(var_name)

    def is_number(self, value:str) -> bool:
        try:
            int(value)
            return True
        except ValueError:
            return False


    def compile_if_else(self, if_else_clause:IfElseClause) -> list[str]:
        pass

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
            elif command.command_type == CommandTypes.IF:
                new_lines = self.__handle_if_else(command)
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
    
    def __set_ra_const(self, value:int) -> list[str]:
        pre_assembly_lines = []
        ra = self.register_manager.ra
        reg_with_const = self.register_manager.check_for_const(value)

        if reg_with_const is not None:
            pre_assembly_lines.append(f"mov ra, {reg_with_const.name}")
            ra.set_mode(RegisterMode.CONST, value)
            return pre_assembly_lines

        pre_assembly_lines.append(f"ldi #{value}")
        ra.set_mode(RegisterMode.CONST, value)

        return pre_assembly_lines
    
    def __set_reg_const(self, reg:Register, value:int) -> list[str]:
        pre_assembly_lines = []
        reg_with_const = self.register_manager.check_for_const(value)

        if reg_with_const is not None:
            pre_assembly_lines.append(f"mov {reg.name}, {reg_with_const.name}")
            reg.set_mode(RegisterMode.CONST, value)
            return pre_assembly_lines

        pre_assembly_lines.extend(self.__set_ra_const(value))
        pre_assembly_lines.append(f"mov {reg.name}, ra")
        reg.set_mode(RegisterMode.CONST, value)

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
            acc = self.register_manager.acc
            
            # Check if new_value is a simple digit
            if command.new_value.isdigit():
                reg_with_const = self.register_manager.check_for_const(int(command.new_value))
                if reg_with_const is not None:
                    pre_assembly_lines.append(f"strl {reg_with_const.name}")
                    return pre_assembly_lines
                
                pre_assembly_lines.extend(self.__set_ra_const(int(command.new_value)))
                pre_assembly_lines.append("strl ra")
                
                return pre_assembly_lines
            
            # Check if new_value contains an addition expression
            elif '+' in command.new_value:
                # Parse the expression (e.g., "var2 + 5")
                parts = [part.strip() for part in command.new_value.split('+')]
                if len(parts) != 2:
                    raise ValueError(f"Invalid expression format: {command.new_value}")
                
                left_part, right_part = parts
                
                # Call __add to compute the expression and store it in ACC
                add_lines = self.__add(left_part, right_part)
                pre_assembly_lines.extend(add_lines)
                
                # Check if ACC contains the correct expression
                if (acc.mode == RegisterMode.TEMPVAR and 
                    acc.get_expression() == command.new_value):
                    # Store ACC to the variable
                    pre_assembly_lines.append("strl acc")
                    return pre_assembly_lines
                else:
                    raise RuntimeError(f"ACC does not contain expected expression: {command.new_value}")
            
            # Check if new_value is a simple variable
            elif self.var_manager.check_variable_exists(command.new_value):
                var_to_assign:Variable = self.var_manager.get_variable(command.new_value)
                raise NotImplementedError("Assignment from variable is not implemented yet.")
            else:
                raise NotImplementedError("Assignment from non-constant or non-variable is not implemented yet.")

        else:
            raise ValueError(f"Unsupported variable type for assignment: {var.var_type}")
        
        return pre_assembly_lines
    
    def __add(self, left:str, right:str) -> list[str]:
        pre_assembly_lines = []
        rd = self.register_manager.rd
        if self.is_number(left):
            raise NotImplementedError("Addition with constant left operand is not implemented yet.")
        
        if not self.var_manager.check_variable_exists(left):
            raise ValueError(f"Left part of addition '{left}' is not a defined variable.")

        if self.is_number(right):
            right_value = int(right)
            pre_assembly_lines.extend(self.__add_var_const(self.var_manager.get_variable(left), right_value))
        else:
            raise NotImplementedError("Addition with non-constant right operand is not implemented yet.")
        
        return pre_assembly_lines

    def __add_var_const(self, left_var:Variable, right_value:int) -> list[str]:
        pre_assembly_lines = []
        rd = self.register_manager.rd
        marl = self.register_manager.marl

        pre_assembly_lines.extend(self.__set_reg_const(rd, right_value))
        pre_assembly_lines.extend(self.__set_marl(left_var))
        pre_assembly_lines.extend(self.__add_ml())
        expression = f"{left_var.name} + {right_value}"
        self.register_manager.acc.set_temp_var_mode(expression)

        return pre_assembly_lines

    def __add_reg(self, register:Register) -> list[str]:
        pre_assembly_lines = []
        rd = self.register_manager.rd
        pre_assembly_lines.append(f"add {register.name}")
        
        
        return pre_assembly_lines
    
    def __add_ml(self) -> list[str]:
        preassembly_lines = []
        preassembly_lines.append("add ml")
        return preassembly_lines
    
    def _compile_condition(self, condition: Condition) -> list[str]:
        pre_assembly_lines = []
        rd = self.register_manager.rd
        if condition.type is None:
            raise ValueError("Condition type is not set. Call __set_type() first.")

        left, right = condition.parts
        if not self.var_manager.check_variable_exists(left):
            raise ValueError(f"Left part of condition '{left}' is not a defined variable.")
        
        left_var = self.var_manager.get_variable(left)
        if self.is_number(right):
            right_value = int(right)
            pre_assembly_lines.extend(self.__set_reg_const(rd, right_value))
            pre_assembly_lines.extend(self.__set_marl(left_var))
            pre_assembly_lines.append("sub ml")

            
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

    def set_grouped_lines(self, grouped_lines:list[Command]) -> None:
        self.grouped_lines = grouped_lines

    def create_context_compiler(self) -> Compiler:
        new_compiler = create_default_compiler()
        new_compiler.var_manager = self.var_manager
        new_compiler.register_manager = self.register_manager
        new_compiler.stack_manager = self.stack_manager
        return new_compiler
    
    @staticmethod
    def __determine_command_type(line:str) -> str:
        if re.match(r'^\w+\s*=\s*.+$', line):
            return "assign"
        return None
            

def create_default_compiler() -> Compiler:
    return Compiler(comment_char='//', variable_start_addr=0x0000, 
                    variable_end_addr=0x0100, memory_size=65536)

if __name__ == "__main__":
    compiler = create_default_compiler()

    
    compiler.load_lines('modules/test2.txt')
    compiler.break_commands()
    compiler.clean_lines()
    compiler.group_commands()
    compiler.compile_lines()
    l = compiler._compile_condition(Condition("dene2 == 5"))
    print("Grouped Commands:" + str(compiler.grouped_lines))
    for i in compiler.pre_assembly_lines:
        print(i)
    print("Compiled Condition:" + str(l))

