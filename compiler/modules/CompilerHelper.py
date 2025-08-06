from __future__ import annotations

from dataclasses import dataclass
from VariableManager import VarTypes, Variable, ByteVariable, VarManager
from StackManager import StackManager
from LabelManager import LabelManager
from RegisterManager import RegisterManager, RegisterMode, Register, TempVarMode
from ConditionHelper import IfElseClause, ConditionTypes
import CompilerStaticMethods as CompilerStaticMethods
import re

from Commands import *


class Compiler:
    def __init__(self, comment_char:str, variable_start_addr:int = 0x0000, 
                 variable_end_addr:int = 0x0100, 
                 stack_start_addr:int=0x0100, 
                 stack_size:int = 256,
                 memory_size:int = 65536):
        
        self.comment_char = comment_char
        self.variable_start_addr = variable_start_addr
        self.variable_end_addr = variable_end_addr
        self.stack_start_addr = stack_start_addr
        self.stack_size = stack_size
        self.memory_size = memory_size

        if stack_size != 256:
            raise ValueError("Stack size must be 256 bytes.")
        
        self.comment_char = comment_char
        self.var_manager = VarManager(variable_start_addr, variable_end_addr, memory_size)
        self.register_manager = RegisterManager()
        self.stack_manager = StackManager(stack_start_addr, memory_size)
        self.label_manager = LabelManager()
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
    def copy_commpiler_as_context(self) -> Compiler:
        new_compiler = Compiler(self.comment_char, 
                                self.variable_start_addr, 
                                self.variable_end_addr, 
                                self.stack_start_addr, 
                                self.stack_size,
                                self.memory_size)
        new_compiler.var_manager = self.var_manager
        new_compiler.register_manager = self.register_manager
        new_compiler.stack_manager = self.stack_manager
        new_compiler.label_manager = self.label_manager
        return new_compiler

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
            pre_assembly_lines.extend(self.__set_marl(new_var))
            pre_assembly_lines.extend(self.__set_ra_const(command.var_value))
            pre_assembly_lines.append("strl ra")

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

    def __mov_marl_to_reg(self, reg:Register) -> list[str]:
        pre_assembly_lines = []
        marl = self.register_manager.marl

        if marl.mode == RegisterMode.ADDR:
            pre_assembly_lines.append(f"ldrl {reg.name}")
            reg.set_variable(marl.variable, RegisterMode.VALUE)
        else:
            raise ValueError("MARL must be set to an address before moving to a register.")
        
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
    
    def __mov_var_to_var(self, left_var:Variable, right_var:Variable) -> list[str]: 
        """Move value from right variable to left, ensuring types match."""
        pre_assembly_lines = []
        marl = self.register_manager.marl
        if left_var.address == right_var.address:
            return pre_assembly_lines
        
        if left_var.value_type != right_var.value_type:
            raise ValueError(f"Cannot move variable of type {right_var.value_type} to {left_var.value_type}")


        right_var_reg = self.register_manager.check_for_variable(right_var.name)

        if right_var_reg is not None:
            pre_assembly_lines.append(self.__set_marl(left_var))
            pre_assembly_lines.append(f"strl {right_var_reg.name}")
            return pre_assembly_lines
        
        print(right_var, marl.variable)
        if marl.variable.name == right_var.name and marl.mode == RegisterMode.ADDR:
            pre_assembly_lines.append(f"ldrl rd")
            self.register_manager.rd.set_variable(right_var, RegisterMode.VALUE)
            pre_assembly_lines.extend(self.__set_marl(left_var))
            pre_assembly_lines.append("strl rd")
            return pre_assembly_lines

        pre_assembly_lines.extend(self.__set_reg_variable(self.register_manager.rd, right_var))
        pre_assembly_lines.extend(self.__set_marl(left_var))
        pre_assembly_lines.append("strl rd")
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
    
    def __set_reg_variable(self, reg:Register, variable:Variable) -> list[str]:
        pre_assembly_lines = []
        reg_with_var:Register = self.register_manager.check_for_variable(variable)
        
        if reg_with_var is not None:
            if reg_with_var.name == reg.name:
                return pre_assembly_lines
            pre_assembly_lines.append(f"mov {reg.name}, {reg_with_var.name}")
            reg.set_variable(variable, RegisterMode.VALUE)
            return pre_assembly_lines
        
        pre_assembly_lines.extend(self.__set_marl(variable))
        pre_assembly_lines.append(f"ldrl {reg.name}")
        reg.set_variable(variable, RegisterMode.VALUE)

        return pre_assembly_lines
    
    def __assign_variable(self, command:AssignCommand) -> list[str]:
        pre_assembly_lines = []
        var:Variable = self.var_manager.get_variable(command.var_name)
        
        if var is None:
            raise ValueError(f"Cannot assign to undefined variable: {command.var_name}")
        
        if type(var) == VarTypes.BYTE.value:  
            ra = self.register_manager.ra
            rd = self.register_manager.rd
            acc = self.register_manager.acc
            
            # Check if new_value is a simple digit
            if command.new_value.isdigit():
                reg_with_const = self.register_manager.check_for_const(int(command.new_value))
                if reg_with_const is not None:
                    if reg_with_const.name == ra.name:
                        pre_assembly_lines.append(f"mov {rd.name}, {reg_with_const.name}")
                        rd.set_variable(var, RegisterMode.VALUE)
                        pre_assembly_lines.extend(self.__set_marl(var))
                        pre_assembly_lines.append("strl rd")
                        return pre_assembly_lines
                    pre_assembly_lines.extend(self.__set_marl(var))
                    pre_assembly_lines.append(f"strl {reg_with_const.name}")
                    return pre_assembly_lines
                
                pre_assembly_lines.extend(self.__set_marl(var))
                pre_assembly_lines.extend(self.__set_ra_const(int(command.new_value)))
                pre_assembly_lines.append("strl ra")
                
                return pre_assembly_lines
            
            # Check if new_value contains an addition expression
            elif '+' in command.new_value:
                raise NotImplementedError("Addition expressions are not implemented yet.")
                normalized_expression = self.__normalize_expression(command.new_value)
                
                # Call __evaluate_expression to compute the expression and store it in ACC
                eval_lines = self.__evaluate_expression(normalized_expression)
                pre_assembly_lines.extend(eval_lines)
                
                # Check if ACC contains the correct expression
                if (acc.mode == RegisterMode.TEMPVAR and 
                    acc.get_expression() == normalized_expression):
                    # Store ACC to the variable
                    pre_assembly_lines.append("strl acc")
                    return pre_assembly_lines
                else:
                    raise RuntimeError(f"ACC does not contain expected expression: {normalized_expression}")
            
            # Check if new_value is a simple variable
            elif self.var_manager.check_variable_exists(command.new_value):
                var_to_assign:Variable = self.var_manager.get_variable(command.new_value)
                pre_assembly_lines.extend(self.__mov_var_to_var(var, var_to_assign))
                return pre_assembly_lines
            else:
                raise NotImplementedError("Assignment from non-constant or non-variable is not implemented yet.")

        else:
            raise ValueError(f"Unsupported variable type for assignment: {var.var_type}")
        
        return pre_assembly_lines
    

    def __handle_if_else(self, command:Command) -> list[str]:
        pre_assembly_lines = []
        if not isinstance(command.line, IfElseClause):
            raise ValueError("Command line must be an IfElseClause instance.")
        if_else_clause:IfElseClause = command.line
        
        if if_else_clause.get_if() is None:
            raise ValueError("IfElseClause must have an 'if' condition defined.")
        
        is_contains_else = if_else_clause.is_contains_else()
        is_contains_elif = if_else_clause.is_contains_elif()
        print(f"Contains else: {is_contains_else}, Contains elif: {is_contains_elif}")

        if (not is_contains_else) and (not is_contains_elif):
            compiled_condition = self._compile_condition(if_else_clause.get_if().condition)
            print(f"Compiled condition: {compiled_condition}")
            pre_assembly_lines.extend(compiled_condition)
            if_label = self.label_manager.create_if_label()
            pre_assembly_lines.extend(self.__set_prl_as_label(if_label))
            
            condition_type = if_else_clause.get_if().condition.type
            pre_assembly_lines.append(CompilerStaticMethods.get_inverted_jump_str(condition_type))

            self.register_manager.reset_change_detector()
            if_context_compiler = self.create_context_compiler()
            if_context_compiler.grouped_lines = if_else_clause.get_if().get_lines()
            if_context_compiler.compile_lines()
            if_compiled_lines = if_context_compiler.pre_assembly_lines
            pre_assembly_lines.extend(if_compiled_lines)
            del if_context_compiler
            pre_assembly_lines.append(f"{if_label}:")
            print("changed regs:", [reg.name for reg in self.register_manager.changed_registers])
            self.register_manager.set_changed_registers_as_unknown()
            return pre_assembly_lines
            
        else:
            raise NotImplementedError("If-Else chains with 'elif' or 'else' are not implemented yet.")
        pass
    
    def __set_prl_as_label(self, label_name:str) -> list[str]:
        pre_assembly_lines = []
        label = self.label_manager.get_label(label_name)
        if label is None:
            raise ValueError(f"Label '{label_name}' does not exist.")
        
        pre_assembly_lines.append(f"ldi @{label}")
        pre_assembly_lines.append("mov prl, ra")
        self.register_manager.prl.set_label_mode(label)
        self.register_manager.ra.set_unknown_mode()

        return pre_assembly_lines
    def __normalize_expression(self, expression: str) -> str:
        """Normalize expression by removing extra spaces and ensuring consistent formatting"""
        # Remove all spaces and then add proper spacing around operators
        expression = expression.replace(' ', '')
        expression = expression.replace('+', ' + ')
        return expression
    
    def __evaluate_expression(self, expression: str) -> list[str]:
        """Evaluate an expression and store the result in ACC register"""
        raise NotImplementedError("Expression evaluation is not implemented yet.")
        pre_assembly_lines = []
        
        # to postfix for braces, +, - , * and / operations
        stack = []
        postfix = []
        # Supported operators and their precedence
        precedence = {'+': 1, '-': 1}
        operators = set(precedence.keys())
        tokens = re.findall(r'\w+|\d+|[+\-()]', expression)

        # Shunting Yard Algorithm: infix to postfix
        for token in tokens:
            if token.isdigit() or self.var_manager.check_variable_exists(token):
                postfix.append(token)
            elif token in operators:
                while (stack and stack[-1] in operators and
                    precedence[stack[-1]] >= precedence[token]):
                    postfix.append(stack.pop())
                stack.append(token)
            elif token == '(':
                stack.append(token)
            elif token == ')':
                while stack and stack[-1] != '(':
                    postfix.append(stack.pop())
                stack.pop()

        while stack:
            postfix.append(stack.pop())

        # Evaluate postfix and generate assembly
        eval_stack = []
        for token in postfix:
            if token.isdigit() or self.var_manager.check_variable_exists(token):
                eval_stack.append(token)
            elif token in operators:
                right = eval_stack.pop()
                left = eval_stack.pop()
            # Load left operand into RD
            if left.isdigit():
                pre_assembly_lines.extend(self.__set_reg_const(self.register_manager.rd, int(left)))
            else:
                var_left = self.var_manager.get_variable(left)
                pre_assembly_lines.extend(self.__set_marl(var_left))
                pre_assembly_lines.append("ldl rd")
            # Add/Sub right operand to RD and store result in ACC
            if right.isdigit():
                pre_assembly_lines.extend(self.__set_ra_const(int(right)))
            else:
                var_right = self.var_manager.get_variable(right)
                pre_assembly_lines.extend(self.__set_marl(var_right))
                pre_assembly_lines.append("ldl ra")
            if token == '+':
                pre_assembly_lines.append("add ra")
            elif token == '-':
                pre_assembly_lines.append("sub ra")
            # After operation, result is in ACC, push a dummy for stack logic
            eval_stack.append("acc")
        
        return pre_assembly_lines    
    
    def __add(self, left:str, right:str) -> list[str]:
        """Legacy method for simple two-term addition - now uses __evaluate_expression"""
        expression = f"{left} + {right}"
        normalized_expression = self.__normalize_expression(expression)
        return self.__evaluate_expression(normalized_expression)

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
    
    def directly_compile_lines(self, lines:list[str]) -> list[str]:
        """Directly compile a list of lines without grouping or pre-processing."""
        self.lines = lines
        self.break_commands()
        self.clean_lines()
        self.group_commands()
        self.compile_lines()
        return self.pre_assembly_lines

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

    
    compiler.load_lines('files/test2.txt')
    compiler.break_commands()
    compiler.clean_lines()
    compiler.group_commands()
    compiler.compile_lines()
    #l = compiler._compile_condition(Condition("dene2 == 5"))
    print("Grouped Commands:" + str(compiler.grouped_lines))
    for i in compiler.pre_assembly_lines:
        print(i)
    #print("Compiled Condition:" + str(l))

