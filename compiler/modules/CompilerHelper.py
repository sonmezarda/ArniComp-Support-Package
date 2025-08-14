from __future__ import annotations

from dataclasses import dataclass
from VariableManager import VarTypes, Variable, ByteVariable, VarManager
from StackManager import StackManager
from LabelManager import LabelManager
from RegisterManager import RegisterManager, RegisterMode, Register, TempVarMode
from ConditionHelper import IfElseClause, Condition, WhileClause
import CompilerStaticMethods as CompilerStaticMethods
import re

from Commands import *
from RegTags import AbsAddrTag, SymbolBaseTag, ElementTag

MAX_LDI = 0b1111111  # Maximum value for LDI instruction (7 bits)
MAX_LOW_ADDRESS = 0b11111111  # Maximum low address for LDI instruction (8 bits)

class Compiler:
    def __init__(self, comment_char: str, variable_start_addr: int = 0x0000,
                 variable_end_addr: int = 0x0100,
                 stack_start_addr: int = 0x0100,
                 stack_size: int = 256,
                 memory_size: int = 65536):
        self.comment_char = comment_char
        self.variable_start_addr = variable_start_addr
        self.variable_end_addr = variable_end_addr
        self.stack_start_addr = stack_start_addr
        self.stack_size = stack_size
        self.memory_size = memory_size
        self.assembly_lines = []

        if stack_size != 256:
            raise ValueError("Stack size must be 256 bytes.")

        self.var_manager = VarManager(variable_start_addr, variable_end_addr, memory_size)
        self.register_manager = RegisterManager()
        self.stack_manager = StackManager(stack_start_addr, memory_size)
        self.label_manager = LabelManager()
        self.lines = []
        # Simple object-like macro defines: {name: replacement}
        self.defines = {}

    def load_lines(self, filename:str) -> None:
        with open(filename, 'r') as file:
            self.lines = file.readlines()
    
    def break_commands(self) -> None:
        # Run preprocessor to handle #def before tokenizing
        self.__preprocess_lines()
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
        if self.grouped_lines is None:
            raise ValueError("Commands must be grouped before compilation.")
        print("Grouped lines to compile: ", self.grouped_lines)
        for command in self.grouped_lines:
            if type(command) is VarDefCommand:     
                if command.var_type == VarTypes.BYTE:
                    self.__create_var_with_value(command)
                elif command.var_type == VarTypes.BYTE_ARRAY:
                    raise NotImplementedError("Array initialization (e.g., byte[3] a = [...]) henüz desteklenmiyor.")
                else:
                    raise ValueError(f"Unsupported variable type: {command.var_type}")
            elif type(command) is VarDefCommandWithoutValue:
                if command.var_type == VarTypes.BYTE: 
                    self.__create_var(command)
                elif command.var_type == VarTypes.BYTE_ARRAY:
                    self.__create_var(command)
                else:
                    raise ValueError(f"Unsupported variable type: {command.var_type}")
            elif type(command) is AssignCommand:
                self.__assign_variable(command)
            elif type(command) is FreeCommand:
                self.__free_variable(command)
            elif type(command) is Command and command.command_type == CommandTypes.IF:
                self.__handle_if_else(command)
            elif type(command) is Command and command.command_type == CommandTypes.WHILE:
                self.__handle_while(command)
            elif type(command) is IfElseClause:
                # Nested if-else clause'ları da işle
                self.__handle_if_else(Command(CommandTypes.IF, command))
            else:
                raise ValueError(f"Unsupported command type: {type(command)} - {command}")
        return self.assembly_lines

    def __create_var_with_value(self, command:VarDefCommand) -> int:
        new_var = self.var_manager.create_variable(
                    var_name=command.var_name, 
                    var_type=command.var_type, 
                    var_value=command.var_value)
        
        if command.var_type == VarTypes.BYTE:
            # Set MAR first, then RA, then store (keeps optimal instruction order)
            self.__set_mar(new_var)
            self.__set_ra_const(command.var_value)
            self.__store_with_current_mar(new_var, self.register_manager.ra)

            self.register_manager.marl.set_variable(new_var, RegisterMode.ADDR)

        else:
            raise ValueError(f"Unsupported variable type: {command.var_type}")
        
        return self.__get_assembly_lines_len()

    def __create_var(self, command:VarDefCommandWithoutValue)-> int:
        if command.var_type == VarTypes.BYTE_ARRAY:
            if command.array_length is None:
                raise ValueError("Array length must be specified for BYTE_ARRAY.")
            new_var:Variable = self.var_manager.create_array_variable(var_name=command.var_name, var_type=command.var_type, array_len=command.array_length, var_value=[0]*command.array_length)
        else:
            new_var:Variable = self.var_manager.create_variable(var_name=command.var_name, var_type=command.var_type, var_value=0)
        return self.__get_assembly_lines_len()
    
    def __free_variable(self, command:FreeCommand) -> int:
        if not self.var_manager.check_variable_exists(command.var_name):
            raise ValueError(f"Variable '{command.var_name}' is not defined.")
        
        var:Variable = self.var_manager.get_variable(command.var_name)
        if var is None:
            raise ValueError(f"Variable '{command.var_name}' is not defined.")
        
        self.var_manager.free_variable(var.name)
        
        return self.__get_assembly_lines_len()
    def __get_assembly_lines_len(self) -> int:
        if not self.assembly_lines:
            return 0
        return len(self.assembly_lines)
    
    def __set_mar(self, var:Variable) -> int:
        if var.address <= MAX_LOW_ADDRESS:
            self.__set_marl(var)
        else:
            self.__set_marl(var)
            self.__set_marh(var)
        return self.__get_assembly_lines_len()

    def __set_mar_abs(self, address: int) -> int:
        """Set MAR to an absolute address (low/optional high). Keeps register cache tags."""
        # small fast path: if MARL already holds this addr low
        marl = self.register_manager.marl
        marh = self.register_manager.marh
        ra = self.register_manager.ra
        low = address & 0xFF
        high = (address >> 8) & 0xFF

        # Reuse if possible
        if marl.mode in [RegisterMode.ADDR, RegisterMode.ADDR_LOW] and marl.tag is not None and isinstance(marl.tag, AbsAddrTag):
            if (marl.tag.addr & 0xFF) == low:
                # ensure MARH matches when needed
                if address > MAX_LOW_ADDRESS:
                    if marh.mode == RegisterMode.ADDR_HIGH and marh.tag and isinstance(marh.tag, AbsAddrTag) and ((marh.tag.addr >> 8) & 0xFF) == high:
                        return self.__get_assembly_lines_len()
                else:
                    return self.__get_assembly_lines_len()

        # set MARL
        if low <= MAX_LDI:
            self.__add_assembly_line(f"ldi #{low}")
            self.__add_assembly_line("mov marl, ra")
            ra.set_mode(RegisterMode.CONST, low)
        else:
            self.__build_const_in_reg(low, marl)
        # invalidate stale var binding and tag MARL
        try:
            marl.set_unknown_mode()
        except Exception:
            pass
        try:
            marl.tag = AbsAddrTag(address)
        except Exception:
            pass

        # set MARH if needed
        if address > MAX_LOW_ADDRESS:
            if high <= MAX_LDI:
                self.__add_assembly_line(f"ldi #{high}")
                self.__add_assembly_line("mov marh, ra")
                ra.set_mode(RegisterMode.CONST, high)
            else:
                self.__build_const_in_reg(high, marh)
            try:
                marh.set_unknown_mode()
            except Exception:
                pass
            try:
                marh.tag = AbsAddrTag(address)
            except Exception:
                pass
        return self.__get_assembly_lines_len()
    
    def __set_marh(self, var:Variable) -> int:
        marh = self.register_manager.marh
        ra = self.register_manager.ra
        high_addr = var.get_high_address()

        if marh.variable == var and marh.mode == RegisterMode.ADDR_HIGH:
            return self.__get_assembly_lines_len()
        
        if marh.variable != None and marh.variable.get_high_address() == var.get_high_address():
            marh.set_variable(var, RegisterMode.ADDR_HIGH)
            return self.__get_assembly_lines_len()
        
         # if var high_addr in another register
        if ra.variable == var:
            if ra.mode == RegisterMode.ADDR_HIGH:
                self.__add_assembly_line("mov marh, ra")
                marh.set_variable(var, RegisterMode.ADDR_HIGH)
                return self.__get_assembly_lines_len()
        elif ra.mode == RegisterMode.CONST and ra.value == var.get_high_address():
            self.__add_assembly_line("mov marh, ra")
            marh.set_variable(var, RegisterMode.ADDR_HIGH)
            return self.__get_assembly_lines_len()

        # Build/load constant into MARH
        if high_addr <= MAX_LDI:
            self.__add_assembly_line(f"ldi #{high_addr}")
            self.__add_assembly_line("mov marh, ra")
            ra.set_mode(RegisterMode.CONST, high_addr)
        else:
            self.__build_const_in_reg(high_addr, marh)
        marh.set_variable(var, RegisterMode.ADDR_HIGH)

    def __set_marl(self, var:Variable) -> int:
        marl = self.register_manager.marl
        ra = self.register_manager.ra
        low_addr = var.get_low_address()
        is_addr_fit_low = var.address == var.get_low_address()

        # If MARL already contains the exact same variable
        if marl.variable == var and marl.mode in [RegisterMode.ADDR, RegisterMode.ADDR_LOW]:
            return self.__get_assembly_lines_len()
        
        # Check if another variable in MARL has the same address (rare case)
        if (marl.variable != None and 
            marl.variable != var and 
            marl.variable.get_low_address() == var.get_low_address()):
            if is_addr_fit_low:
                marl.set_variable(var, RegisterMode.ADDR)
            else:
                marl.set_variable(var, RegisterMode.ADDR_LOW)
            return self.__get_assembly_lines_len()
        
        # if var addr in another register
        if ra.variable == var:
            if ra.mode == RegisterMode.ADDR:
                self.__add_assembly_line("mov marl, ra")
                marl.set_variable(var, RegisterMode.ADDR)
                return self.__get_assembly_lines_len()
            elif ra.mode == RegisterMode.ADDR_LOW:
                self.__add_assembly_line("mov marl, ra")
                if is_addr_fit_low:
                    marl.set_variable(var, RegisterMode.ADDR)
                else:
                    marl.set_variable(var, RegisterMode.ADDR_LOW)
                return self.__get_assembly_lines_len()
        elif ra.mode == RegisterMode.CONST and ra.value == var.get_low_address():
            self.__add_assembly_line("mov marl, ra")
            if is_addr_fit_low:
                marl.set_variable(var, RegisterMode.ADDR)
            else:
                marl.set_variable(var, RegisterMode.ADDR_LOW)
            return self.__get_assembly_lines_len()
            
        # Load/build constant into MARL
        if low_addr <= MAX_LDI:
            self.__add_assembly_line(f"ldi #{low_addr}")
            self.__add_assembly_line("mov marl, ra")
            if is_addr_fit_low:
                marl.set_variable(var, RegisterMode.ADDR)
                ra.set_variable(var, RegisterMode.ADDR)
            else:
                ra.set_variable(var, RegisterMode.ADDR_LOW)
                marl.set_variable(var, RegisterMode.ADDR_LOW)
        else:
            self.__build_const_in_reg(low_addr, marl)
            if is_addr_fit_low:
                marl.set_variable(var, RegisterMode.ADDR)
            else:
                marl.set_variable(var, RegisterMode.ADDR_LOW)

        return self.__get_assembly_lines_len()

    def __ldi(self, value:int) -> int:
        if value > MAX_LDI:
            raise ValueError(f"Value {value} exceeds maximum LDI value of {MAX_LDI}.")
        self.__add_assembly_line(f"ldi #{value}")
        self.register_manager.ra.set_mode(RegisterMode.CONST, value)
        return self.__get_assembly_lines_len()

    def __build_const_in_reg(self, value: int, target_reg: Register) -> int:
        """Build any 8-bit constant (0-255) into specified register using optimal combination of LDI/ADDI/SUBI.
        Strategy: Find the most efficient method among:
        1. Single LDI (if <= 127)
        2. LDI + ADDI sequence 
        3. LDI + LDI + ADD sequence
        4. 127*2 - SUBI sequence
        """
        ra = self.register_manager.ra
        rd = self.register_manager.rd
        acc = self.register_manager.acc
        if value > 255:
            raise ValueError(f"Value {value} exceeds maximum 8-bit value of 255.")
        
        target = value & 0xFF
        if target <= MAX_LDI:
            self.__ldi(target)
            if target_reg.name != "ra":
                self.__add_assembly_line(f"mov {target_reg.name}, ra")
                target_reg.set_mode(RegisterMode.CONST, target)
            return self.__get_assembly_lines_len()

        # Calculate cost for different strategies
        strategies = []
        
        # Strategy 1: LDI base + ADDI remainder
        for base in range(MAX_LDI, 0, -1):  # Try from 127 down
            remainder = target - base
            if remainder > 0:
                addi_steps = (remainder + 6) // 7  # Ceiling division for 7-bit chunks
                if remainder <= 7 * 7:  # Max 7 ADDI instructions (7*7=49 max remainder)
                    cost = 3 + (2 * addi_steps)  # ldi + mov rd,ra + N*(addi + mov rd,acc) + mov target,acc
                    strategies.append(('addi', base, remainder, cost))
        
        # Strategy 2: LDI + LDI + ADD (for values that can be sum of two LDIs)
        for base1 in range(MAX_LDI, target // 2, -1):  # First LDI
            base2 = target - base1
            if base2 <= MAX_LDI and base2 > 0:
                cost = 4  # ldi + mov rd,ra + ldi + add ra + mov target,acc
                strategies.append(('add_two_ldi', base1, base2, cost))
        
        # Strategy 3: 127*2 - SUBI (for values close to 254)
        if target >= 128 and target <= 254:
            remainder = 254 - target
            if remainder >= 0:  # Only valid for values <= 254
                subi_steps = (remainder + 6) // 7
                if remainder <= 7 * 7:  # Max 7 SUBI instructions
                    cost = 4 + subi_steps  # ldi + mov rd,ra + add rd + N*subi + mov target,acc
                    strategies.append(('subi_from_254', 127, remainder, cost))
        
        # Strategy 4: 255 = 127*2 + 1 (special case for maximum value)
        if target == 255:
            cost = 5  # ldi + mov rd,ra + add rd + addi + mov target,acc
            strategies.append(('add_254_plus_1', 127, 1, cost))
        
        # Choose the strategy with minimum cost
        if not strategies:
            # Fallback to simple ADDI approach
            self.__ldi(MAX_LDI)
            remainder = target - MAX_LDI
            self.__add_assembly_line("mov rd, ra")
            rd.set_mode(RegisterMode.CONST, MAX_LDI)
            
            current = MAX_LDI
            while remainder > 0:
                step = min(7, remainder)
                self.__add_assembly_line(f"addi #{step}")
                current += step
                if remainder > step:  # Don't mov rd,acc on last iteration
                    self.__add_assembly_line("mov rd, acc")
                    rd.set_mode(RegisterMode.CONST, current)
                remainder -= step
            
            self.__add_assembly_line(f"mov {target_reg.name}, acc")
            target_reg.set_mode(RegisterMode.CONST, current)
            ra.set_unknown_mode()
            return self.__get_assembly_lines_len()
        
        # Execute the best strategy
        best_strategy = min(strategies, key=lambda x: x[3])
        strategy_type, param1, param2, cost = best_strategy
        
        if strategy_type == 'addi':
            base, remainder = param1, param2
            self.__ldi(base)
            self.__add_assembly_line("mov rd, ra")
            rd.set_mode(RegisterMode.CONST, base)
            
            current = base
            while remainder > 0:
                step = min(7, remainder)
                self.__add_assembly_line(f"addi #{step}")
                current += step
                if remainder > step:  # Don't mov rd,acc on last iteration
                    self.__add_assembly_line("mov rd, acc")
                    rd.set_mode(RegisterMode.CONST, current)
                remainder -= step
            
            self.__add_assembly_line(f"mov {target_reg.name}, acc")
            target_reg.set_mode(RegisterMode.CONST, current)
            
        elif strategy_type == 'add_two_ldi':
            base1, base2 = param1, param2
            self.__ldi(base1)
            self.__add_assembly_line("mov rd, ra")
            self.__ldi(base2)
            self.__add_assembly_line("add ra")  # acc = rd + ra
            self.__add_assembly_line(f"mov {target_reg.name}, acc")
            target_reg.set_mode(RegisterMode.CONST, target)
            
        elif strategy_type == 'add_254_plus_1':
            # Build 255 = 254 + 1
            # First create 254 = 127 * 2
            self.__ldi(MAX_LDI)  # Load 127 into RA
            ra.set_mode(RegisterMode.CONST, 127)
            
            self.__add_assembly_line("mov rd, ra")  # Copy 127 to RD
            rd.set_mode(RegisterMode.CONST, 127)
            
            self.__add_assembly_line("add rd")  # ACC = RD + RA = 127 + 127 = 254
            acc.set_mode(RegisterMode.CONST, 254)
            
            self.__add_assembly_line("mov rd, acc")  # Store 254 in RD
            rd.set_mode(RegisterMode.CONST, 254)
            
            # ADDI semantics: ACC = RD + immediate = 254 + 1 = 255
            self.__add_assembly_line("addi #1")  
            acc.set_mode(RegisterMode.CONST, 255)
            
            # Move to target if needed
            if target_reg != acc:
                self.__add_assembly_line(f"mov {target_reg.name}, acc")
                target_reg.set_mode(RegisterMode.CONST, 255)
            
        elif strategy_type == 'subi_from_254':
            _, remainder = param1, param2
            self.__ldi(MAX_LDI)  # 127
            self.__add_assembly_line("mov rd, ra")
            self.__add_assembly_line("add rd")  # ACC = 254
            
            current = 254
            while remainder > 0:
                step = min(7, remainder)
                self.__add_assembly_line(f"subi #{step}")
                current -= step
                remainder -= step
            
            self.__add_assembly_line(f"mov {target_reg.name}, acc")
            target_reg.set_mode(RegisterMode.CONST, current)
        
        ra.set_unknown_mode()  # RA is used for intermediate calculations
        return self.__get_assembly_lines_len()

    def __build_const_in_ra(self, value: int) -> int:
        """Legacy wrapper - builds constant in RA register"""
        return self.__build_const_in_reg(value, self.register_manager.ra)

    def __store_with_current_mar(self, var: Variable, src: Register) -> int:
        """Store using current MAR (does not modify MAR registers)."""
        if var.address <= MAX_LOW_ADDRESS:
            self.__add_assembly_line(f"strl {src.name}")
        else:
            self.__add_assembly_line(f"strh {src.name}")
        return self.__get_assembly_lines_len()

    def __store_with_current_mar_abs(self, address:int, src:Register) -> int:
        if address <= MAX_LOW_ADDRESS:
            self.__add_assembly_line(f"strl {src.name}")
        else:
            self.__add_assembly_line(f"strh {src.name}")
        return self.__get_assembly_lines_len()

    def __load_with_current_mar_abs(self, address:int, dst:Register) -> int:
        """Load from absolute address already in MAR into dst register (chooses ldrl/ldrh)."""
        if address <= MAX_LOW_ADDRESS:
            self.__add_assembly_line(f"ldrl {dst.name}")
        else:
            self.__add_assembly_line(f"ldrh {dst.name}")
        # Content doesn't map to a named variable; mark dst unknown to avoid stale bindings
        try:
            dst.set_unknown_mode()
        except Exception:
            pass
        return self.__get_assembly_lines_len()

    # New helpers: MAR-aware load/store
    def __store_to_var(self, var: Variable, src: Register) -> int:
        """Store src register to memory at var, using strl/strh depending on address width."""
        self.__set_mar(var)
        if var.address <= MAX_LOW_ADDRESS:
            self.__add_assembly_line(f"strl {src.name}")
        else:
            self.__add_assembly_line(f"strh {src.name}")
        return self.__get_assembly_lines_len()

    def __load_var_to_reg(self, var: Variable, dst: Register) -> int:
        """Load memory at var to dst register, using ldrl/ldrh depending on address width."""
        self.__set_mar(var)
        if var.address <= MAX_LOW_ADDRESS:
            self.__add_assembly_line(f"ldrl {dst.name}")
        else:
            self.__add_assembly_line(f"ldrh {dst.name}")
        dst.set_variable(var, RegisterMode.VALUE)
        return self.__get_assembly_lines_len()

    def __mov_marl_to_reg(self, reg:Register) -> int:
        marl = self.register_manager.marl
    
        if marl.mode in [RegisterMode.ADDR, RegisterMode.ADDR_LOW]:
            # Decide by the bound variable's address span
            bound_var = marl.variable
            if bound_var is None:
                raise ValueError("MARL has no bound variable to load from.")
            if bound_var.address <= MAX_LOW_ADDRESS:
                self.__add_assembly_line(f"ldrl {reg.name}")
            else:
                self.__add_assembly_line(f"ldrh {reg.name}")
            reg.set_variable(bound_var, RegisterMode.VALUE)
        else:
            raise ValueError("MARL must be set to an address before moving to a register.")
        return self.__get_assembly_lines_len()

    def __set_ra_const(self, value:int) -> int:
        ra = self.register_manager.ra
        reg_with_const = self.register_manager.check_for_const(value)

        if reg_with_const is not None:
            if reg_with_const.name != ra.name:
                self.__add_assembly_line(f"mov ra, {reg_with_const.name}")
            ra.set_mode(RegisterMode.CONST, value)
            return self.__get_assembly_lines_len()

        self.__ldi(value)
        ra.set_mode(RegisterMode.CONST, value)

        return self.__get_assembly_lines_len()

    def __mov_var_to_var(self, left_var:Variable, right_var:Variable) -> int:
        """Move value from right variable to left, ensuring types match."""
        marl = self.register_manager.marl
        if left_var.address == right_var.address:
            return self.__get_assembly_lines_len()
        
        if left_var.value_type != right_var.value_type:
            raise ValueError(f"Cannot move variable of type {right_var.value_type} to {left_var.value_type}")

        right_var_reg = self.register_manager.check_for_variable(right_var.name)

        if right_var_reg is not None:
            # Store directly from existing register into left var
            self.__store_to_var(left_var, right_var_reg)
            return self.__get_assembly_lines_len()
        
        # If MAR is already pointing to right_var, load it
        print(right_var, marl.variable)
        if marl.variable is not None and marl.variable.name == right_var.name and marl.mode in [RegisterMode.ADDR, RegisterMode.ADDR_LOW]:
            self.__load_var_to_reg(right_var, self.register_manager.rd)
            self.__store_to_var(left_var, self.register_manager.rd)
            return self.__get_assembly_lines_len()

        # Otherwise, load right var to RD then store to left
        self.__set_reg_variable(self.register_manager.rd, right_var)
        self.__store_to_var(left_var, self.register_manager.rd)
        return self.__get_assembly_lines_len()

    def __set_reg_const(self, reg:Register, value:int) -> list[str]:
        reg_with_const = self.register_manager.check_for_const(value)

        if reg_with_const is not None:
            if reg_with_const.name != reg.name:
                self.__add_assembly_line(f"mov {reg.name}, {reg_with_const.name}")
            reg.set_mode(RegisterMode.CONST, value)
            return self.__get_assembly_lines_len()

        self.__set_ra_const(value)
        if reg.name != 'ra':
            self.__add_assembly_line(f"mov {reg.name}, ra")
        reg.set_mode(RegisterMode.CONST, value)

        return self.__get_assembly_lines_len()
    
    def __set_reg_variable(self, reg:Register, variable:Variable) ->int:
        pre_assembly_lines = []
        reg_with_var:Register = self.register_manager.check_for_variable(variable)
        
        if reg_with_var is not None:
            if reg_with_var.name == reg.name:
                return self.__get_assembly_lines_len()
            self.__add_assembly_line(f"mov {reg.name}, {reg_with_var.name}")
            reg.set_variable(variable, RegisterMode.VALUE)
            return self.__get_assembly_lines_len()
        
        # Use MAR-aware load
        self.__load_var_to_reg(variable, reg)
        return self.__get_assembly_lines_len()
    
    def __assign_variable(self, command:AssignCommand) -> list[str]:
        pre_assembly_lines = []
        var:Variable = self.var_manager.get_variable(command.var_name)
        
        if var is None:
            raise ValueError(f"Cannot assign to undefined variable: {command.var_name}")
        
        # Handle array element assignment: arr[idx] = value;
        if command.is_array:
            if not isinstance(var, Variable):
                raise ValueError("Invalid variable for array assignment")
            if type(var) != VarTypes.BYTE_ARRAY.value:
                raise ValueError(f"Variable '{var.name}' is not an array.")

            # Only constant index supported for now
            idx_expr = command.index_expr
            if idx_expr is None:
                raise ValueError("Array index missing.")
            # If index is constant: fast absolute addressing path
            if idx_expr.isdigit():
                idx = int(idx_expr)
                elem_size = VarTypes.BYTE_ARRAY.value.get_size()
                address = var.address + idx * elem_size

                rhs = command.new_value
                if rhs.isdigit():
                    value = int(rhs)
                    ra = self.register_manager.ra
                    reg_with_const = self.register_manager.check_for_const(value)
                    if reg_with_const is not None and reg_with_const.name != 'ra':
                        self.__set_mar_abs(address)
                        self.__store_with_current_mar_abs(address, reg_with_const)
                        return self.__get_assembly_lines_len()
                    self.__set_mar_abs(address)
                    self.__set_ra_const(value)
                    self.__store_with_current_mar_abs(address, ra)
                    return self.__get_assembly_lines_len()
                else:
                    # RHS is variable: load into RD then store
                    rhs_name = rhs.strip()
                    if not self.var_manager.check_variable_exists(rhs_name):
                        raise NotImplementedError("Array assignment RHS must be const or existing byte variable.")
                    rhs_var = self.var_manager.get_variable(rhs_name)
                    self.__set_mar_abs(address)
                    self.__set_reg_variable(self.register_manager.rd, rhs_var)
                    self.__store_with_current_mar_abs(address, self.register_manager.rd)
                    return self.__get_assembly_lines_len()

            # Dynamic index path (low-page arrays without overflow): idx is a byte variable
            idx_name = idx_expr.strip()
            if not self.var_manager.check_variable_exists(idx_name):
                raise NotImplementedError("Array index must be a constant or an existing byte variable.")
            idx_var = self.var_manager.get_variable(idx_name)

            # Only support arrays fully within low page [0x00:0xFF] for now
            base_low = var.get_low_address()
            base_high = var.get_high_address()
            arr_span_ok = (base_high == 0) and (base_low + var.size - 1 <= 0xFF)
            if not arr_span_ok:
                raise NotImplementedError("Dynamic index supported only for arrays fully in low page without overflow.")

            rd = self.register_manager.rd
            ra = self.register_manager.ra

            # RD <- index value (loads from memory; MARL may be changed inside)
            self.__set_reg_variable(rd, idx_var)
            # RA <- base_low constant
            self.__set_ra_const(base_low)
            # ACC <- RD + RA ; MARL <- ACC
            self.__add_reg(ra)
            self.__add_assembly_line("mov marl, acc")
            # Invalidate MARL cache since it's now a computed address, not bound to any variable
            try:
                self.register_manager.marl.set_unknown_mode()
            except Exception:
                pass

            # RHS
            rhs = command.new_value.strip()
            if rhs.isdigit():
                value = int(rhs)
                self.__set_ra_const(value)
                self.__add_assembly_line("strl ra")
                return self.__get_assembly_lines_len()
            else:
                if not self.var_manager.check_variable_exists(rhs):
                    raise NotImplementedError("Array assignment RHS must be const or existing byte variable.")
                # Save computed low address in RD, load RHS to RA (will disturb MAR), then restore MARL, then STRL RA
                self.__add_assembly_line("mov rd, acc")
                self.register_manager.rd.set_mode(RegisterMode.CONST, None)  # mark unknown content typewise
                rhs_var = self.var_manager.get_variable(rhs)
                self.__set_reg_variable(ra, rhs_var)
                self.__add_assembly_line("mov marl, rd")
                # Invalidate MARL cache after restoring from RD (dynamic address)
                try:
                    self.register_manager.marl.set_unknown_mode()
                except Exception:
                    pass
                self.__add_assembly_line("strl ra")
                return self.__get_assembly_lines_len()

        if type(var) == VarTypes.BYTE.value:  
            ra = self.register_manager.ra
            rd = self.register_manager.rd
            acc = self.register_manager.acc
            # Array element read on RHS: b = arr[idx]
            m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\[(.+)\]$', command.new_value.strip())
            if m:
                arr_name, idx_expr = m.group(1), m.group(2).strip()
                if not self.var_manager.check_variable_exists(arr_name):
                    raise ValueError(f"Array '{arr_name}' is not defined.")
                arr_var = self.var_manager.get_variable(arr_name)
                if type(arr_var) != VarTypes.BYTE_ARRAY.value:
                    raise ValueError(f"'{arr_name}' bir dizi değil.")

                # Constant index: absolute address load
                if idx_expr.isdigit():
                    idx = int(idx_expr)
                    elem_size = VarTypes.BYTE_ARRAY.value.get_size()
                    address = arr_var.address + idx * elem_size
                    self.__set_mar_abs(address)
                    self.__load_with_current_mar_abs(address, rd)
                    self.__store_to_var(var, rd)
                    return self.__get_assembly_lines_len()

                # Dynamic index: low-page arrays without overflow
                if not self.var_manager.check_variable_exists(idx_expr):
                    raise NotImplementedError("Dizi indeks değişkeni bulunamadı (sabit ya da tanımlı byte olmalı).")
                idx_var = self.var_manager.get_variable(idx_expr)
                base_low = arr_var.get_low_address()
                base_high = arr_var.get_high_address()
                arr_span_ok = (base_high == 0) and (base_low + arr_var.size - 1 <= 0xFF)
                if not arr_span_ok:
                    raise NotImplementedError("Dinamik indeks okuma şimdilik sadece low-page ve taşma yokken destekleniyor.")

                # RD <- idx; RA <- base_low; ACC <- RD + RA; MARL <- ACC; invalidate cache
                self.__set_reg_variable(rd, idx_var)
                self.__set_ra_const(base_low)
                self.__add_reg(ra)
                self.__add_assembly_line("mov marl, acc")
                try:
                    self.register_manager.marl.set_unknown_mode()
                except Exception:
                    pass
                # Load element and store to var
                self.__add_assembly_line("ldrl rd")
                try:
                    self.register_manager.rd.set_unknown_mode()
                except Exception:
                    pass
                self.__store_to_var(var, rd)
                return self.__get_assembly_lines_len()
            
            # Check if new_value is a simple digit
            if command.new_value.isdigit():
                reg_with_const = self.register_manager.check_for_const(int(command.new_value))
                if reg_with_const is not None:
                    if reg_with_const.name == ra.name:
                        # Preserve RA before setting MAR, then store via RD
                        self.__add_assembly_line(f"mov {rd.name}, {ra.name}")
                        rd.set_mode(RegisterMode.CONST, int(command.new_value))
                        self.__set_mar(var)
                        self.__store_with_current_mar(var, rd)
                        return self.__get_assembly_lines_len()
                    # Use the cached const register directly
                    self.__set_mar(var)
                    self.__store_with_current_mar(var, reg_with_const)
                    return self.__get_assembly_lines_len()

                # No cached const: set MAR first, then RA, then store
                self.__set_mar(var)
                self.__set_ra_const(int(command.new_value))
                self.__store_with_current_mar(var, ra)

                return self.__get_assembly_lines_len()
            
            # Check if new_value contains an addition expression
            elif '+' in command.new_value or '-' in command.new_value:
                normalized_expression = self.__normalize_expression(command.new_value)
                
                # Call __evaluate_expression to compute the expression and store it in ACC
                eval_lines = self.__evaluate_expression(normalized_expression)
                
                # Check if ACC contains the correct expression
                if (acc.mode == RegisterMode.TEMPVAR and 
                    acc.get_expression() == normalized_expression):
                    # Store ACC to the variable: set MAR explicitly, then STRL/STRH
                    self.__set_mar(var)
                    if var.address <= MAX_LOW_ADDRESS:
                        self.__add_assembly_line("strl acc")
                    else:
                        self.__add_assembly_line("strh acc")
                    return self.__get_assembly_lines_len()
                else:
                    raise RuntimeError(f"ACC does not contain expected expression: {normalized_expression}")
            
            # Check if new_value is a simple variable
            elif self.var_manager.check_variable_exists(command.new_value):
                var_to_assign:Variable = self.var_manager.get_variable(command.new_value)
                (self.__mov_var_to_var(var, var_to_assign))
                return self.__get_assembly_lines_len()
            else:
                raise NotImplementedError("Assignment from non-constant or non-variable is not implemented yet.")

        else:
            raise ValueError(f"Unsupported variable type for assignment: {var.var_type}")
        
        return self.__get_assembly_lines_len()
    

    def __handle_if_else(self, command:Command) -> int:
        if not isinstance(command.line, IfElseClause):
            raise ValueError("Command line must be an IfElseClause instance.")
        if_else_clause:IfElseClause = command.line
        
        if if_else_clause.get_if() is None:
            raise ValueError("IfElseClause must have an 'if' condition defined.")
        
        is_contains_else = if_else_clause.is_contains_else()
        is_contains_elif = if_else_clause.is_contains_elif()

        if (not is_contains_else) and (not is_contains_elif):
            # set flags for if condition
            self.__compile_condition(if_else_clause.get_if().condition)

            # create context compiler for 'if' block
            self.register_manager.reset_change_detector()
            if_context_compiler = self.create_context_compiler()
            if_context_compiler.grouped_lines = if_else_clause.get_if().get_lines()
            if_context_compiler.compile_lines() 
            if_inner_len = if_context_compiler.__get_assembly_lines_len()
            # create & set label for 'if' block
            if_label, if_label_position = self.label_manager.create_if_label(self.__get_assembly_lines_len() + if_inner_len)
            self.__set_prl_as_label(if_label, if_label_position)
            
            condition_type = if_else_clause.get_if().condition.type
            # Add jump instruction based on condition type
            self.__add_assembly_line(CompilerStaticMethods.get_inverted_jump_str(condition_type))
            # add 'if' block assembly lines
            self.__add_assembly_line(if_context_compiler.assembly_lines)
            self.register_manager.set_changed_registers_as_unknown()
            # Update label position
            self.label_manager.update_label_position(if_label, self.__get_assembly_lines_len())
            del if_context_compiler
            # add label for 'if' block
            self.__add_assembly_line(f"{if_label}:")
            print("changed regs:", [reg.name for reg in self.register_manager.changed_registers])
            self.register_manager.set_changed_registers_as_unknown()
            return self.__get_assembly_lines_len()
            
        elif is_contains_else and not is_contains_elif:
            self.__compile_condition(if_else_clause.get_if().condition)

            self.register_manager.ra.set_unknown_mode()
            self.register_manager.prl.set_unknown_mode()

            self.register_manager.reset_change_detector()
            if_context_compiler = self.create_context_compiler()
            if_context_compiler.grouped_lines = if_else_clause.get_if().get_lines()
            if_context_compiler.compile_lines() 
            if_inner_len = if_context_compiler.__get_assembly_lines_len()
            # create & set label for 'if' block
            if_label, if_label_position = self.label_manager.create_if_label(self.__get_assembly_lines_len() + if_inner_len)
            self.__set_prl_as_label(if_label, if_label_position)
            
            condition_type = if_else_clause.get_if().condition.type
            # Add jump instruction based on condition type
            self.__add_assembly_line(CompilerStaticMethods.get_inverted_jump_str(condition_type))
            # add 'if' block assembly lines
            self.__add_assembly_line(if_context_compiler.assembly_lines)
            self.register_manager.set_changed_registers_as_unknown()
            # Update label position
            self.label_manager.update_label_position(if_label, self.__get_assembly_lines_len())
            del if_context_compiler
            
            self.register_manager.ra.set_unknown_mode()
            self.register_manager.prl.set_unknown_mode()
            else_context_compiler = self.create_context_compiler()
            else_context_compiler.grouped_lines = if_else_clause.get_else().get_lines()
            else_context_compiler.compile_lines()
            else_inner_len = else_context_compiler.__get_assembly_lines_len()

            else_label, else_label_position = self.label_manager.create_else_label(self.__get_assembly_lines_len() + else_inner_len)
            self.__set_prl_as_label(else_label, else_label_position)

            self.__add_assembly_line("jmp")
            self.__add_assembly_line(f"{if_label}:")

            self.__add_assembly_line(else_context_compiler.assembly_lines)
            self.__add_assembly_line(f"{else_label}:")
            self.register_manager.set_changed_registers_as_unknown()
            # add label for 'if' block
        else:
            raise NotImplementedError("If-Else chains with 'elif' or 'else' are not implemented yet.")
        pass

    def __handle_while(self, command: Command) -> int:
        if not isinstance(command.line, WhileClause):
            raise ValueError("Command line must be a WhileClause instance.")
        while_clause: WhileClause = command.line

        # Create labels for loop start and exit using LabelManager helpers
        start_label_name, _ = self.label_manager.create_while_start_label(self.__get_assembly_lines_len())
        self.__add_assembly_line(f"{start_label_name}:")

        # Evaluate condition and jump to end if false
        self.__compile_condition(while_clause.condition)

        # Compile body in a context to measure length
        body_comp = self.create_context_compiler()
        body_comp.grouped_lines = while_clause.get_lines()
        body_comp.compile_lines()
        body_len = body_comp.__get_assembly_lines_len()

        # Create end label and set PRL to it for conditional jump
        end_label, _ = self.label_manager.create_while_end_label(self.__get_assembly_lines_len() + body_len + 3)
        self.__set_prl_as_label(end_label, self.label_manager.get_label(end_label))
        self.__add_assembly_line(CompilerStaticMethods.get_inverted_jump_str(while_clause.condition.type))

        # Emit body
        self.__add_assembly_line(body_comp.assembly_lines)
        self.register_manager.set_changed_registers_as_unknown()

        # Jump back to start
        self.__set_prl_as_label(start_label_name, self.label_manager.get_label(start_label_name))
        self.__add_assembly_line("jmp")

        # Place end label at current position
        self.label_manager.update_label_position(end_label, self.__get_assembly_lines_len())
        self.__add_assembly_line(f"{end_label}:")
        return self.__get_assembly_lines_len()

    def __set_prl_as_label(self, label_name:str, label_position:int) -> int:
        if label_position + 2 > 0b1111111:
            raise NotImplementedError("Label position over 7 bits is not supported yet.")

        if not self.label_manager.is_label_defined(label_name):
            raise ValueError(f"Label '{label_name}' does not exist.")
        
        self.__add_assembly_line(f"ldi @{label_name}")
        self.__add_assembly_line("mov prl, ra")
        self.register_manager.prl.set_label_mode(label_name)
        self.register_manager.ra.set_unknown_mode()

        return self.__get_assembly_lines_len()

    def __normalize_expression(self, expression: str) -> str:
        """Normalize expression by removing extra spaces and ensuring consistent formatting"""
        # Remove all spaces and then add proper spacing around operators
        expression = expression.replace(' ', '')
        expression = expression.replace('+', ' + ')
        expression = expression.replace('-', ' - ')
        return expression
    
    def __evaluate_expression(self, expression: str) -> int:
        """
        Evaluate a + b - c ... style expressions.
        Each term can be:
        - decimal constant
        - defined variable name
        Final result is left in ACC.
        RD holds the running sum/difference for chaining.
        """
        # 1) Normalize and tokenize
        expr = self.__normalize_expression(expression)  # "a + 5 - b" -> "a + 5 - b"
        if not expr:
            raise ValueError("Empty expression.")

        tokens = [t for t in expr.split(' ') if t]

        def is_op(tok: str) -> bool:
            return tok in ('+', '-')

        def is_int(tok: str) -> bool:
            try:
                int(tok)
                return True
            except ValueError:
                return False

        # 2) İlk terimi RD'ye yükle
        rd = self.register_manager.rd
        ra = self.register_manager.ra
        acc = self.register_manager.acc

        idx = 0
        first = tokens[idx]
        if is_op(first):
            raise ValueError(f"Expression cannot start with operator: '{expression}'")

        if is_int(first):
            self.__set_reg_const(rd, int(first))
        else:
            if not self.var_manager.check_variable_exists(first):
                raise ValueError(f"Unknown variable in expression: '{first}'")
            var0 = self.var_manager.get_variable(first)
            self.__set_reg_variable(rd, var0)

        idx += 1

        # 3) (+/- term)* döngüsü
        while idx < len(tokens):
            op = tokens[idx]
            if not is_op(op):
                raise ValueError(f"Expected '+' or '-', got '{op}' in '{expression}'")
            idx += 1
            if idx >= len(tokens):
                raise ValueError(f"Trailing operator '{op}' without term in '{expression}'")

            term = tokens[idx]

            if is_int(term):
                self.__set_reg_const(ra, int(term))
                if op == '+':
                    self.__add_reg(ra)     # ACC = RD + RA
                else:
                    self.__add_assembly_line(f"sub {ra.name}")  # ACC = RD - RA
                self.__add_assembly_line("mov rd, acc")
                self.register_manager.rd.set_unknown_mode()
            else:
                if not self.var_manager.check_variable_exists(term):
                    raise ValueError(f"Unknown variable in expression: '{term}'")
                v = self.var_manager.get_variable(term)
                self.__set_marl(v)
                if op == '+':
                    self.__add_ml()        # ACC = RD + [MAR]
                else:
                    self.__add_assembly_line("sub ml")  # ACC = RD - [MAR]
                self.__add_assembly_line("mov rd, acc")
                self.register_manager.rd.set_unknown_mode()

            idx += 1

        # 5) ACC'nin ifade tuttuğunu işaretle
        self.register_manager.acc.set_temp_var_mode(expr)

        return self.__get_assembly_lines_len()


    
    def __add(self, left:str, right:str) -> list[str]:
        """Legacy method for simple two-term addition - now uses __evaluate_expression"""
        expression = f"{left} + {right}"
        normalized_expression = self.__normalize_expression(expression)
        return self.__evaluate_expression(normalized_expression)

    def __add_var_const(self, left_var:Variable, right_value:int) -> int:
        pre_assembly_lines = []
        rd = self.register_manager.rd
        marl = self.register_manager.marl

        self.__set_reg_const(rd, right_value)
        self.__set_marl(left_var)
        self.__add_ml()
        expression = f"{left_var.name} + {right_value}"
        self.register_manager.acc.set_temp_var_mode(expression)

        return self.__get_assembly_lines_len()

    def __add_reg(self, register:Register) -> int:
        pre_assembly_lines = []
        rd = self.register_manager.rd
        self.__add_assembly_line(f"add {register.name}")

        return self.__get_assembly_lines_len()
    
    def __add_ml(self) -> int:
        
        self.assembly_lines.append("add ml")
        return self.__get_assembly_lines_len()

    def __compile_condition(self, condition: Condition) -> int:
        rd = self.register_manager.rd
        if condition.type is None:
            raise ValueError("Condition type is not set. Call __set_type() first.")

        left, right = condition.parts
        if not self.var_manager.check_variable_exists(left):
            raise ValueError(f"Left part of condition '{left}' is not a defined variable.")
        left_var = self.var_manager.get_variable(left)

        # Load RIGHT into RD
        if self.is_number(right):
            self.__set_reg_const(rd, int(right))
        else:
            if not self.var_manager.check_variable_exists(right):
                raise ValueError(f"Right part of condition '{right}' is not a defined variable.")
            right_var = self.var_manager.get_variable(right)
            self.__set_reg_variable(rd, right_var)

        # Compare RD (A) with ML (B) where ML is LEFT
        self.__set_marl(left_var)
        self.__add_assembly_line("sub ml")

        return self.__get_assembly_lines_len()
    
    @staticmethod
    def __group_line_commands(lines:list[str]) -> list[Command]:
        grouped_lines:list[Command] = []
        lindex = 0
        if isinstance(lines, str):
            lines = [lines]
        while lindex < len(lines):
            line = lines[lindex]
            print(f"Processing line {lindex}: '{line}'")
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
            elif FreeCommand.match_regex(line):
                print(f"'{line}' matches FreeCommand regex")
                grouped_lines.append(FreeCommand(line))
                lindex += 1
            elif line.startswith('if '):
                print(f"'{line}' starts an if clause")
                nested_count = 0
                group = []
                while lindex < len(lines):
                    group.append(lines[lindex])
                    if lines[lindex].startswith('endif'):
                        nested_count -= 1
                        if nested_count < 1:
                            lindex += 1
                            break
                    elif lines[lindex].startswith('if '):
                        nested_count += 1
                    lindex += 1
                
                grouped_if_else = IfElseClause.group_nested_if_else(group)
                print(f"Grouped if-else lines: {grouped_if_else}")
                if_clause = IfElseClause.parse_from_lines(grouped_if_else)
                print(if_clause)
                if_clause.apply_to_all_lines(lambda lines: Compiler.__group_line_commands(lines) if isinstance(lines, list) else Compiler.__group_line_commands([lines]))
                print(f"Processed if-else clause: {if_clause}")
                grouped_lines.append(Command(CommandTypes.IF, if_clause))

            elif line.startswith('while '):
                print(f"'{line}' starts a while clause")
                # Collect until matching 'endwhile'
                nested = 0
                group = []
                header = line
                group.append(header)
                lindex += 1
                while lindex < len(lines):
                    cur = lines[lindex]
                    if cur.startswith('while '):
                        nested += 1
                    elif cur.startswith('endwhile'):
                        if nested == 0:
                            break
                        nested -= 1
                    group.append(cur)
                    lindex += 1
                if lindex >= len(lines) or not lines[lindex].startswith('endwhile'):
                    raise ValueError("Missing 'endwhile' for while loop")
                # Parse into WhileClause
                cond = header[len('while '):].strip()
                wc = WhileClause(cond)
                # Body is group[1:]; convert entire body into Commands, preserving nested if/else
                body = group[1:]
                body_cmds = Compiler.__group_line_commands(body)
                wc.lines = body_cmds
                grouped_lines.append(Command(CommandTypes.WHILE, wc))
                # Skip the 'endwhile'
                lindex += 1

            elif line.startswith('endif'):
                print(f"'{line}' is an endif, skipping")
                lindex += 1
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
        new_compiler.label_manager = self.label_manager
        new_compiler.assembly_lines = []
        new_compiler.defines = self.defines.copy()
        return new_compiler
    
    def directly_compile_lines(self, lines: list[str]) -> list[str]:
        """Directly compile a list of lines without grouping or pre-processing."""
        self.lines = lines
        self.break_commands()
        self.clean_lines()
        self.group_commands()
        self.compile_lines()
        return self.assembly_lines

    def __preprocess_lines(self) -> None:
        """Process #def directives and apply object-like macro replacements to self.lines."""
        if not self.lines:
            return
        raw_lines = self.lines
        defs: dict[str, str] = {}
        kept: list[str] = []
        def_re = re.compile(r'^\s*#def\s+([A-Za-z_][A-Za-z0-9_]*)\s+(.+?)\s*$')
        for ln in raw_lines:
            s = ln.strip()
            if not s or s.startswith(self.comment_char):
                kept.append(ln)
                continue
            m = def_re.match(ln)
            if m:
                name = m.group(1)
                repl = m.group(2)
                defs[name] = repl
            else:
                kept.append(ln)
        if defs:
            self.defines.update(defs)
        if not self.defines:
            self.lines = kept
            return
        # Build per-name regexes for whole-identifier replacement
        patterns = {name: re.compile(rf'(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])') for name in self.defines}
        def apply_defs(s: str) -> str:
            out = s
            # Limit nested expansion to avoid infinite loops
            for _ in range(5):
                changed = False
                for name, pat in patterns.items():
                    new_out = pat.sub(self.defines[name], out)
                    if new_out != out:
                        changed = True
                        out = new_out
                if not changed:
                    break
            return out
        self.lines = [apply_defs(ln) for ln in kept]

    

    def __add_assembly_line(self, lines:str|list[str]) -> int:

        if isinstance(lines, list):
            self.assembly_lines.extend(lines)
            return self.assembly_lines.__len__()
        if not isinstance(lines, str):
            raise ValueError("Line must be a string or a list of strings.")

        self.assembly_lines.append(lines)
        return self.assembly_lines.__len__()
    
    def clear_assembly_lines(self) -> None:
        """Clear all assembly lines."""
        self.assembly_lines.clear()

    def get_assembly_lines(self) -> list[str]:
        """Get all assembly lines."""
        return self.assembly_lines
    
    @staticmethod
    def __determine_command_type(line:str) -> str:
        if re.match(r'^\w+\s*=\s*.+$', line):
            return "assign"
        return None
            

def create_default_compiler() -> Compiler:
    return Compiler(comment_char='//', variable_start_addr=0x0000, 
                    variable_end_addr=0x0200, memory_size=65536)

if __name__ == "__main__":
    compiler = create_default_compiler()

    
    compiler.load_lines('files/test3.txt')
    compiler.break_commands()
    compiler.clean_lines()
    compiler.group_commands()
    print("Grouped Commands:" + str(compiler.grouped_lines))
    compiler.compile_lines()
    
    for i in compiler.assembly_lines:
        print(i)
    #print("Compiled Condition:" + str(l))

