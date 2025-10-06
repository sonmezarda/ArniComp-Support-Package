from __future__ import annotations

import re
import logging
from dataclasses import dataclass

from VariableManager import VarTypes, Variable, ByteVariable, VarManager
from StackManager import StackManager
from LabelManager import LabelManager
from RegisterManager import RegisterManager, RegisterMode, Register
from ConditionHelper import IfElseClause, Condition, WhileClause, DirectAssemblyClause, WhileTypes
import CompilerStaticMethods as CSM
from MyEnums import ExpressionTypes
from Commands import *
from RegTags import AbsAddrTag

# Create logger for this module
logger = logging.getLogger(__name__)

MAX_LDI = 127  # 7-bit LDI instruction max value
MAX_LOW_ADDRESS = 255  # 8-bit low address max value

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

        self.var_manager = VarManager(variable_start_addr, variable_end_addr, memory_size)
        self.register_manager = RegisterManager()
        self.stack_manager = StackManager(stack_start_addr, memory_size)
        self.label_manager = LabelManager()
        self.lines = []
        self.defines = {}  # Preprocessor macro definitions

    def load_lines(self, filename:str) -> None:
        with open(filename, 'r') as file:
            self.lines = file.readlines()
    
    def break_commands(self) -> None:
        """Process preprocessor directives and remove comments"""
        self.__preprocess_lines()
        self.lines = [line.split(';')[0].strip() for line in self.lines 
                     if line.strip() and not line.startswith(self.comment_char)]

    def clean_lines(self) -> None:
        """Normalize whitespace in lines"""
        self.lines = [re.sub(r'\s+', ' ', line).strip() for line in self.lines 
                     if line.strip() and not line.startswith(self.comment_char)]
    
    def is_variable_defined(self, var_name: str) -> bool:
        return self.var_manager.check_variable_exists(var_name)

    def is_number(self, value: str) -> bool:
        try:
            int(value)
            return True
        except ValueError:
            return False
        
    def copy_compiler_as_context(self) -> Compiler:
        """Create a copy of compiler with shared managers for nested contexts"""
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

    def compile_lines(self):
        """Compile grouped command lines into assembly"""
        if self.grouped_lines is None:
            raise ValueError("Commands must be grouped before compilation.")
        logger.debug(f"Compiling {len(self.grouped_lines)} grouped lines")
        for command in self.grouped_lines:
            if type(command) is VarDefCommand:     
                if command.var_type == VarTypes.BYTE:
                    self.__create_var_with_value(command)
                elif command.var_type == VarTypes.BYTE_ARRAY:
                    raise NotImplementedError("Array initialization not yet supported.")
                else:
                    raise ValueError(f"Unsupported variable type: {command.var_type}")
            elif type(command) is VarDefCommandWithoutValue:
                if command.var_type in [VarTypes.BYTE, VarTypes.BYTE_ARRAY, VarTypes.UINT16]:
                    self.__create_var(command)
                else:
                    raise ValueError(f"Unsupported variable type: {command.var_type}")
            elif type(command) is AssignCommand:
                self.__assign_variable(command)
            elif type(command) is FreeCommand:
                self.__free_variable(command)
            elif type(command) is StoreToDirectAddressCommand:
                self.__store_to_direct_address(command)
            elif type(command) is Command and command.command_type == CommandTypes.IF:
                self.__handle_if_else(command)
            elif type(command) is Command and command.command_type == CommandTypes.WHILE:
                self.__handle_while(command)
            elif type(command) is DirectAssemblyCommand:
                self.__handle_direct_assembly(command)
            elif type(command) is IfElseClause:
                self.__handle_if_else(Command(CommandTypes.IF, command))
            else:
                raise ValueError(f"Unsupported command type: {type(command)} - {command}")
        return self.assembly_lines

    def __handle_direct_assembly(self, command: DirectAssemblyCommand):
        """Insert raw assembly lines directly"""
        for line in command.assembly_lines:
            self.__add_assembly_line(line)
        return self.__get_assembly_lines_len()

    def __store_to_direct_address(self, command: StoreToDirectAddressCommand) -> int:
        """Store value to absolute memory address"""
        return self.__assign_store_to_abs(command.addr, command.new_value)

    def __create_var_with_value(self, command: VarDefCommand) -> int:
        """Create and initialize variable with value"""
        new_var = self.var_manager.create_variable(
                    var_name=command.var_name, 
                    var_type=command.var_type, 
                    var_value=command.var_value)
        
        if command.var_type == VarTypes.BYTE:
            self.__set_mar_abs(new_var.address)
            self.__set_ra_const(command.var_value)
            self.__store_with_current_mar_abs(new_var.address, self.register_manager.ra)
            self.register_manager.marl.set_variable(new_var, RegisterMode.ADDR)
        else:
            raise ValueError(f"Unsupported variable type: {command.var_type}")
        
        return self.__get_assembly_lines_len()

    # === Unified assignment helpers ===
    def __rhs_needs_memory(self, expr: str) -> bool:
        """Check if evaluating expression requires memory loads"""
        s = expr.strip()
        if s.startswith('*'):
            return True
        # Check for numeric literal
        try:
            if CSM.convert_to_decimal(s) is not None:
                return False
        except Exception:
            pass
        # Check for array access
        if re.search(r"[A-Za-z_][A-Za-z0-9_]*\s*\[", s):
            return True
        # Check for variables in expression
        norm = self.__normalize_expression(s)
        tokens = [t for t in norm.split(' ') if t and t not in ['+', '-']]
        for t in tokens:
            try:
                if CSM.convert_to_decimal(t) is not None:
                    continue
            except Exception:
                pass
            if self.var_manager.check_variable_exists(t):
                return True
        return False

    def __compute_rhs(self, expr: str) -> Register:
        """Compute RHS expression and return the register holding the result (RA/ACC/RD)."""
        s = expr.strip()
        # Direct absolute memory dereference: *<number>
        if s.startswith('*'):
            inner = s[1:].strip()
            try:
                address = CSM.convert_to_decimal(inner)
            except Exception:
                address = None
            if address is None:
                raise ValueError(f"Invalid dereference address: {s}")
            # Point MAR to address and load into RD
            self.__set_mar_abs(address)
            if address <= MAX_LOW_ADDRESS:
                self.__add_assembly_line("ldrl rd")
            else:
                self.__add_assembly_line("ldrh rd")
            try:
                self.register_manager.rd.set_unknown_mode()
            except Exception:
                pass
            return self.register_manager.rd
        # Array read: name[idx]
        m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\[(.+)\]$', s)
        if m:
            arr_name, idx_expr = m.group(1), m.group(2).strip()
            if not self.var_manager.check_variable_exists(arr_name):
                raise ValueError(f"Array '{arr_name}' is not defined.")
            arr_var = self.var_manager.get_variable(arr_name)
            if type(arr_var) != VarTypes.BYTE_ARRAY.value:
                raise ValueError(f"'{arr_name}' is not an array.")
            # Set MAR to element, load into RD
            self.__set_mar_array_elem(arr_var, idx_expr)
            if arr_var.address <= MAX_LOW_ADDRESS and (arr_var.get_high_address() == 0):
                self.__add_assembly_line("ldrl rd")
            else:
                self.__add_assembly_line("ldrh rd")
            try:
                self.register_manager.rd.set_unknown_mode()
            except Exception:
                pass
            return self.register_manager.rd

        # Has operators? use existing expression evaluator into ACC
        if ('+' in s) or ('-' in s) or ('&' in s):
            norm = self.__normalize_expression(s)
            self.__evaluate_expression(norm)  # leaves result in ACC
            return self.register_manager.acc

        # Pure literal
        try:
            val = CSM.convert_to_decimal(s)
            if val is not None:
                self.__set_ra_const(val)
                return self.register_manager.ra
        except Exception:
            pass

        # Single variable
        if self.var_manager.check_variable_exists(s):
            v = self.var_manager.get_variable(s)
            self.__set_reg_variable(self.register_manager.rd, v)
            return self.register_manager.rd

        raise ValueError(f"Unsupported RHS expression: {expr}")

    def __set_mar_array_elem(self, arr_var: Variable, index_expr: str) -> int:
        """Point MAR to arr[index]. Supports constant index and low-page dynamic index."""
        idx_s = index_expr.strip()
        # Constant index
        try:
            idx = CSM.convert_to_decimal(idx_s)
            if idx is not None:
                address = arr_var.address + int(idx)
                return self.__set_mar_abs(address)
        except Exception:
            pass
        # Dynamic low-page index
        if not self.var_manager.check_variable_exists(idx_s):
            raise NotImplementedError("Array index must be a constant or an existing byte variable.")
        idx_var = self.var_manager.get_variable(idx_s)
        base_low = arr_var.get_low_address()
        base_high = arr_var.get_high_address()
        # Low-page, no overflow assumption
        if not ((base_high == 0) and (base_low + arr_var.size - 1 <= 0xFF)):
            raise NotImplementedError("Dynamic array index supported only in low page without overflow.")
        # RD <- idx
        self.__set_reg_variable(self.register_manager.rd, idx_var)
        # RA <- base_low
        self.__set_ra_const(base_low)
        # ACC <- RD + RA ; MARL <- ACC
        self.__add_reg(self.register_manager.ra)
        self.__add_assembly_line("mov marl, acc")
        try:
            self.register_manager.marl.set_unknown_mode()
        except Exception:
            pass
        return self.__get_assembly_lines_len()

    def __assign_store_to_abs(self, address: int, rhs_expr: str) -> int:
        """Unified direct absolute store with smart MAR ordering."""
        needs_mem = self.__rhs_needs_memory(rhs_expr)
        src_reg: Register
        if needs_mem:
            # compute first, then set MAR
            src_reg = self.__compute_rhs(rhs_expr)
            self.__set_mar_abs(address)
        else:
            # set MAR first, then compute
            self.__set_mar_abs(address)
            src_reg = self.__compute_rhs(rhs_expr)

        if address <= MAX_LOW_ADDRESS:
            self.__add_assembly_line(f"strl {src_reg.name}")
        else:
            self.__add_assembly_line(f"strh {src_reg.name}")
        # Invalidate any cached register bound to the stored var (if tracked)
        if address < self.var_manager.mem_end_addr and address >= self.var_manager.mem_start_addr:
            var_in_mem = self.var_manager.get_variable_from_address(address)
            if var_in_mem is not None:
                reg_with_var = self.register_manager.check_for_variable(var_in_mem)
                if reg_with_var is not None and reg_with_var.mode == RegisterMode.VALUE:
                    reg_with_var.set_unknown_mode()
        return self.__get_assembly_lines_len()

    def __compile_assign_var(self, var: Variable, rhs_expr: str) -> int:
        """var = expr; Choose MAR ordering smartly based on RHS memory needs."""
        if type(var) is VarTypes.BYTE.value:
            needs_mem = self.__rhs_needs_memory(rhs_expr)
            src_reg: Register
            if needs_mem:
                src_reg = self.__compute_rhs(rhs_expr)
                self.__set_mar_abs(var.address)
            else:
                self.__set_mar_abs(var.address)
                src_reg = self.__compute_rhs(rhs_expr)
            # store (var is byte for now)
            if var.address <= MAX_LOW_ADDRESS:
                self.__add_assembly_line(f"strl {src_reg.name}")
            else:
                self.__add_assembly_line(f"strh {src_reg.name}")
            return self.__get_assembly_lines_len()
        elif type(var) is VarTypes.UINT16.value:
            exp_type = CSM.get_expression_type(rhs_expr)
            if exp_type == ExpressionTypes.SINGLE_DEC or exp_type == ExpressionTypes.ALL_DEC:

                if exp_type == ExpressionTypes.SINGLE_DEC:
                    rhs_dec = CSM.convert_to_decimal(rhs_expr)    
                elif exp_type == ExpressionTypes.ALL_DEC:     
                    rhs_dec = eval(rhs_expr)

                if rhs_dec is None:
                    raise ValueError("Invalid UINT16 value.")

                rhs_byte_count = CSM.get_decimal_byte_count(rhs_dec)
                if rhs_byte_count > 2:
                    raise ValueError("UINT16 value out of range (0-65535).")
                
                rhs_bytes = CSM.get_decimal_bytes(rhs_dec)
                logger.debug(f"Variable definition: {var.name} at address 0x{var.address:04X}")
                self.__set_mar_abs(var.address)
                self.__set_ra_const(rhs_bytes[0])
                self.__store_with_current_mar_abs(    var.address, self.register_manager.ra)

                self.__set_mar_abs(var.address+1)
                self.__set_ra_const(rhs_bytes[1])
                self.__store_with_current_mar_abs(var.address+1, self.register_manager.ra)
                
                return self.__get_assembly_lines_len()
                
            else:
                raise NotImplementedError("UINT16 assignment only supports direct literals for now.")
            
        else:
            raise ValueError(f"Unsupported variable type for assignment: {type(var)}")


    def __compile_assign_array(self, arr_var: Variable, index_expr: str, rhs_expr: str) -> int:
        """arr[idx] = expr; Set MAR to element, compute RHS with smart ordering, then store."""
        # Decide ordering: if RHS needs memory, compute first; else set target first
        needs_mem = self.__rhs_needs_memory(rhs_expr)
        src_reg: Register
        if needs_mem:
            src_reg = self.__compute_rhs(rhs_expr)
            self.__set_mar_array_elem(arr_var, index_expr)
        else:
            self.__set_mar_array_elem(arr_var, index_expr)
            src_reg = self.__compute_rhs(rhs_expr)
        # store: if constant index, select strl/strh by absolute address; else dynamic index is restricted to low page
        try:
            idx = CSM.convert_to_decimal(index_expr)
        except Exception:
            idx = None
        if idx is not None:
            abs_addr = arr_var.address + int(idx)
            if abs_addr <= MAX_LOW_ADDRESS:
                self.__add_assembly_line(f"strl {src_reg.name}")
            else:
                self.__add_assembly_line(f"strh {src_reg.name}")
        else:
            self.__add_assembly_line(f"strl {src_reg.name}")
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
        """Deprecated compatibility: route through __set_mar_abs."""
        return self.__set_mar_abs(var.address)

    def __set_mar_abs(self, address: int) -> int:
        """Set MAR to an absolute address (low/optional high). Keeps register cache tags."""
        # small fast path: if MARL already holds this addr low
        marl = self.register_manager.marl
        marh = self.register_manager.marh
        ra = self.register_manager.ra
        low = address & 0xFF
        high = (address >> 8) & 0xFF

        # Reuse if possible (based on AbsAddrTag, independent of register.mode)
        if marl.tag is not None and isinstance(marl.tag, AbsAddrTag):
            if (marl.tag.addr & 0xFF) == low:
                # Low byte already correct; update only MARH if needed and return
                if address > MAX_LOW_ADDRESS:
                    # If MARH already correct, nothing to do
                    if marh.tag and isinstance(marh.tag, AbsAddrTag) and ((marh.tag.addr >> 8) & 0xFF) == high:
                        return self.__get_assembly_lines_len()
                    # Otherwise set MARH to 'high' without touching MARL
                    if high <= MAX_LDI:
                        self.__set_ra_const(high)
                        self.__add_assembly_line("mov marh, ra")
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
                else:
                    # Address in low page and MARL already matches; nothing to do
                    return self.__get_assembly_lines_len()

        # set MARL (force LDI to avoid relying on RA-const cache)
        if low <= MAX_LDI:
            self.__ldi(low)
            self.register_manager.ra.set_mode(RegisterMode.CONST, low)
            self.__add_assembly_line("mov marl, ra")
        else:
            # Build directly into MARL (ends with 'mov marl, acc')
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
                self.__ldi(high)
                self.register_manager.ra.set_mode(RegisterMode.CONST, high)
                self.__add_assembly_line("mov marh, ra")
            else:
                # Build directly into MARH (ends with 'mov marh, acc')
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
        """Deprecated compatibility: route through __set_mar_abs."""
        return self.__set_mar_abs(var.address)

    def __set_marl(self, var:Variable) -> int:
        """Deprecated compatibility: route through __set_mar_abs."""
        return self.__set_mar_abs(var.address)

    def __ldi(self, value:int) -> int:
        if value > MAX_LDI:
            raise ValueError(f"Value {value} exceeds maximum LDI value of {MAX_LDI}.")
        self.__add_assembly_line(f"ldi #{value}")
        self.register_manager.ra.set_mode(RegisterMode.CONST, value)
        return self.__get_assembly_lines_len()

    def __ldi(self, value:int) -> int:
        if value > MAX_LDI:
            raise ValueError(f"Value {value} exceeds maximum LDI value of {MAX_LDI}.")
        self.__add_assembly_line(f"ldi #{value}")
        self.register_manager.ra.set_mode(RegisterMode.CONST, value)
        return self.__get_assembly_lines_len()
    
    def __set_msb_ra(self) -> int:
        self.__add_assembly_line("smsbra")
        if self.register_manager.ra.mode == RegisterMode.CONST:
            new_val = self.register_manager.ra.value | 0x80
            self.register_manager.ra.set_mode(RegisterMode.CONST, new_val)
        else:
            self.register_manager.ra.set_unknown_mode()
        return self.__get_assembly_lines_len()
    
    def __mov(self, dst:Register, src:Register) -> int:
        if dst.name == src.name:
            return self.__get_assembly_lines_len()
        if not src.outable:
            raise ValueError(f"Source register {src.name} is not outable.")
        
        if not dst.writable:
            raise ValueError(f"Destination register {dst.name} is not writable.")
        
        self.__add_assembly_line(f"mov {dst.name}, {src.name}")
        if src.mode == RegisterMode.UNKNOWN:
            dst.set_unknown_mode()
        elif src.mode == RegisterMode.CONST:
            dst.set_mode(RegisterMode.CONST, src.value)
        else:
            dst.set_mode(src.mode, src.value, src.variable)
        return self.__get_assembly_lines_len()
    
    # newestIS
    def __build_const_in_reg(self, value: int, target_reg: Register) -> int:
        """
        Build any 8-bit constant (0-255) into specified register using
        """
        ra = self.register_manager.ra
        if value > 255:
            raise ValueError(f"Value {value} exceeds maximum 8-bit value of 255.")
        
        # Reuse existing register with constant if possible
        reg_with_const = self.register_manager.check_for_const(value)
        if reg_with_const is not None:
            # If it's the target reg, nothing to do
            if reg_with_const.name == target_reg.name:
                return self.__get_assembly_lines_len()
            else:
                # Move from existing const reg to target reg if possible
                if reg_with_const.outable:
                    self.__mov(target_reg, reg_with_const)
                    return self.__get_assembly_lines_len()
        
        if value <= MAX_LDI:
            self.__ldi(value)
            if target_reg.name != "ra":
                self.__mov(target_reg, ra)
            return self.__get_assembly_lines_len()

        value_except_msb = value & 0x7F  # lower 7 bits
        self.__ldi(value_except_msb)  # RA <- lower 7 bits
        self.__set_msb_ra()  # RA <- RA | 0x80
        if target_reg.name != "ra":
            self.__mov(target_reg, ra)
        return self.__get_assembly_lines_len()

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

        # Build RA constant efficiently: use LDI if within range, else compose via __build_const_in_reg
        if value <= MAX_LDI:
            self.__ldi(value)
            ra.set_mode(RegisterMode.CONST, value)
        else:
            self.__build_const_in_reg(value, ra)

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
        var = self.var_manager.get_variable(command.var_name)
        if var is None:
            raise ValueError(f"Cannot assign to undefined variable: {command.var_name}")

        if command.is_array:
            if type(var) != VarTypes.BYTE_ARRAY.value:
                raise ValueError(f"Variable '{var.name}' is not an array.")
            if command.index_expr is None:
                raise ValueError("Array index missing.")
            return self.__compile_assign_array(var, command.index_expr, command.new_value)

        if type(var) == VarTypes.BYTE.value or type(var) == VarTypes.UINT16.value:
            return self.__compile_assign_var(var, command.new_value)
        

        raise ValueError(f"Unsupported variable type for assignment: {var.var_type}")
    

    def __handle_if_else(self, command:Command) -> int:
        if not isinstance(command.line, IfElseClause):
            raise ValueError("Command line must be an IfElseClause instance.")
        if_else_clause:IfElseClause = command.line
        
        if if_else_clause.get_if() is None:
            raise ValueError("IfElseClause must have an 'if' condition defined.")
        
        is_contains_else = if_else_clause.is_contains_else()
        is_contains_elif = if_else_clause.is_contains_elif()

        # Case 1: simple IF without else/elif
        if (not is_contains_else) and (not is_contains_elif):
            self.__compile_condition(if_else_clause.get_if().condition)

            self.register_manager.reset_change_detector()
            if_comp = self.create_context_compiler()
            if_comp.grouped_lines = if_else_clause.get_if().get_lines()
            if_comp.compile_lines()
            if_len = if_comp.__get_assembly_lines_len()

            skip_label, _ = self.label_manager.create_if_label(self.__get_assembly_lines_len() + if_len)
            self.__set_prl_as_label(skip_label, self.label_manager.get_label(skip_label))
            self.__add_assembly_line(CSM.get_inverted_jump_str(if_else_clause.get_if().condition.type))
            self.__add_assembly_line(if_comp.assembly_lines)
            self.register_manager.set_changed_registers_as_unknown()
            self.label_manager.update_label_position(skip_label, self.__get_assembly_lines_len())
            self.__add_assembly_line(f"{skip_label}:")
            return self.__get_assembly_lines_len()

        # Case 2: IF with optional ELIFs and optional ELSE
        branches: list[tuple[Condition, Compiler]] = []
        first_if = if_else_clause.get_if()
        # Precompile IF body
        if_comp = self.create_context_compiler()
        if_comp.grouped_lines = first_if.get_lines()
        if_comp.compile_lines()
        branches.append((first_if.condition, if_comp))

        # Precompile ELIF bodies
        for e in if_else_clause.get_elif():
            e_comp = self.create_context_compiler()
            e_comp.grouped_lines = e.get_lines()
            e_comp.compile_lines()
            branches.append((e.condition, e_comp))

        # Precompile ELSE body if present
        else_comp = None
        if is_contains_else:
            else_comp = self.create_context_compiler()
            else_comp.grouped_lines = if_else_clause.get_else().get_lines()
            else_comp.compile_lines()

        # Reserve END label
        end_est = self.__get_assembly_lines_len() + sum(comp.__get_assembly_lines_len() for _, comp in branches)
        if else_comp is not None:
            end_est += else_comp.__get_assembly_lines_len()
        end_label, _ = self.label_manager.create_else_label(end_est)

        # Emit the chain: for each branch, jump over if false, run body, then jump to END
        for cond, comp in branches:
            # Evaluate and set PRL to skip label
            self.__compile_condition(cond)

            body_len = comp.__get_assembly_lines_len()
            skip_label, _ = self.label_manager.create_if_label(self.__get_assembly_lines_len() + body_len)
            self.__set_prl_as_label(skip_label, self.label_manager.get_label(skip_label))
            self.__add_assembly_line(CSM.get_inverted_jump_str(cond.type))

            # Body
            self.__add_assembly_line(comp.assembly_lines)
            self.register_manager.set_changed_registers_as_unknown()

            # Jump to END after executing this branch
            self.__set_prl_as_label(end_label, self.label_manager.get_label(end_label))
            self.__add_assembly_line("jmp")

            # Place skip label for next branch
            self.label_manager.update_label_position(skip_label, self.__get_assembly_lines_len())
            self.__add_assembly_line(f"{skip_label}:")

        # ELSE body (if any)
        if else_comp is not None:
            self.__add_assembly_line(else_comp.assembly_lines)
            self.register_manager.set_changed_registers_as_unknown()

        # Place END label
        self.label_manager.update_label_position(end_label, self.__get_assembly_lines_len())
        self.__add_assembly_line(f"{end_label}:")
        return self.__get_assembly_lines_len()

    def __handle_while(self, command: Command) -> int:
        if not isinstance(command.line, WhileClause):
            raise ValueError("Command line must be a WhileClause instance.")
        while_clause: WhileClause = command.line
        logger.debug(f"Processing while loop: type={while_clause.type}, condition='{while_clause.condition}'")
        if while_clause.type == WhileTypes.BYPASS:
            return self.__get_assembly_lines_len()
        elif while_clause.type == WhileTypes.CONDITIONAL:
            # Create labels for loop start and exit
            start_label_name, _ = self.label_manager.create_while_start_label(self.__get_assembly_lines_len())
            # Place loop start label
            self.__add_assembly_line(f"{start_label_name}:")
            # Evaluate condition and jump to end if false
            self.__compile_condition(while_clause.condition)

            # Compile body to measure length
            body_comp = self.create_context_compiler()
            body_comp.grouped_lines = while_clause.get_lines()
            body_comp.compile_lines()
            body_len = body_comp.__get_assembly_lines_len()

            # Create end label and set PRL to it for conditional jump
            end_label, _ = self.label_manager.create_while_end_label(self.__get_assembly_lines_len() + body_len + 3)
            self.__set_prl_as_label(end_label, self.label_manager.get_label(end_label))
            self.__add_assembly_line(CSM.get_inverted_jump_str(while_clause.condition.type))

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
        elif while_clause.type == WhileTypes.INFINITE:
            # Preheader: detect MAR invariance across the loop body and hoist MAR setup if safe
            body_cmds = while_clause.get_lines()
            invariant_addr = self.__analyze_loop_mar_invariance(body_cmds)

            start_label_name, _ = self.label_manager.create_while_start_label(self.__get_assembly_lines_len())
            if invariant_addr is not None:
                # Seed MAR to invariant address before entering loop
                self.__set_mar_abs(invariant_addr)
            self.__add_assembly_line(f"{start_label_name}:")

            body_comp = self.create_context_compiler()
            body_comp.grouped_lines = while_clause.get_lines()
            body_comp.compile_lines()
            body_len = body_comp.__get_assembly_lines_len()
            
            self.__add_assembly_line(body_comp.assembly_lines)
            self.__set_prl_as_label(start_label_name, self.label_manager.get_label(start_label_name))
            self.__add_assembly_line("jmp")
            #self.register_manager.set_changed_registers_as_unknown()
            pass
        else:
            raise TypeError("Unsupported while clause type.")

    # ===== Loop analysis helpers =====
    def __analyze_loop_mar_invariance(self, cmds: list[Command]) -> int | None:
        """Path-sensitive MAR address invariance analysis over the loop body.
        Returns a concrete absolute address if for all possible paths through the body,
        MAR ends at the same address, and at least one command sets it.
        Otherwise returns None.
        """
        ok, init_addr, final_addr = self.__eval_block_mar(None, cmds)
        if not ok or init_addr is None or final_addr is None:
            return None
        return init_addr if init_addr == final_addr else None

    def __eval_block_mar(self, in_addr: int | None, cmds: list[Command]) -> tuple[bool, int | None, int | None]:
        """Evaluate a sequence of commands. Returns (ok, init_addr, out_addr).
        - ok False => unknown
        - init_addr is the first definite MAR address set within the block (or in_addr if none set)
        - out_addr is the definite MAR address after the block
        """
        cur = in_addr
        init = None
        for c in cmds:
            ok, new_cur = self.__apply_cmd_to_mar(cur, c)
            if not ok:
                return False, None, None
            # Record first set address if not yet captured
            if init is None and new_cur is not None and new_cur != cur:
                init = new_cur
            cur = new_cur
        return True, (init if init is not None else in_addr), cur

    def __apply_cmd_to_mar(self, cur_addr: int | None, cmd: Command) -> tuple[bool, int | None]:
        """Apply a single command to MAR state.
        Returns (ok, new_addr) where ok=False indicates unknown.
        """
        # Command wrapper handling
        if isinstance(cmd, Command):
            # IF/ELIF/ELSE chain
            if getattr(cmd, 'command_type', None) == CommandTypes.IF and isinstance(cmd.line, IfElseClause):
                clause: IfElseClause = cmd.line
                outcomes: set[int | None] = set()

                # Helper to eval a branch lines list
                def eval_branch(lines_list):
                    success, _, out = self.__eval_block_mar(cur_addr, lines_list)
                    if not success:
                        return False
                    outcomes.add(out)
                    return True

                # if branch
                if clause.get_if() is not None:
                    if not eval_branch(clause.get_if().get_lines()):
                        return False, None
                # elif branches
                for elif_clause in clause.get_elif():
                    if not eval_branch(elif_clause.get_lines()):
                        return False, None
                # else branch
                has_else = clause.get_else() is not None
                if has_else:
                    if not eval_branch(clause.get_else().get_lines()):
                        return False, None
                else:
                    # No else => path where no branch executes
                    outcomes.add(cur_addr)

                # All possible outcomes must be same definite address
                if None in outcomes or len(outcomes) != 1:
                    return False, None
                only = next(iter(outcomes))
                return True, only

            # Nested while or other controls: unknown
            if getattr(cmd, 'command_type', None) == CommandTypes.WHILE:
                return False, None

            # Direct assembly via wrapper? treat unknown
            if getattr(cmd, 'command_type', None) == CommandTypes.DIRECT_ASSEMBLY:
                return False, None
            # Do NOT return here; allow concrete subclasses below to be checked

        # Direct absolute store: *ABS = expr
        if isinstance(cmd, StoreToDirectAddressCommand):
            try:
                return True, int(cmd.addr)
            except Exception:
                return False, None

        # Assignment: var or array element
        if isinstance(cmd, AssignCommand):
            var = self.var_manager.get_variable(cmd.var_name)
            if cmd.is_array:
                idx_expr = cmd.index_expr
                try:
                    idx = CSM.convert_to_decimal(idx_expr) if idx_expr is not None else None
                except Exception:
                    idx = None
                if idx is None:
                    return False, None  # dynamic index -> unknown
                base = var.address
                try:
                    return True, int(base + int(idx))
                except Exception:
                    return False, None
            else:
                return True, var.address

        # Var defs/frees or direct asm mutate MAR unpredictably in our model
        if isinstance(cmd, (VarDefCommand, VarDefCommandWithoutValue, FreeCommand, DirectAssemblyCommand)):
            return False, None

        # Unknown command types: assume no MAR effect
        return True, cur_addr

    def __set_prl_as_label(self, label_name:str, label_position:int) -> int:
        if label_position + 2 > 0b1111111:
            raise NotImplementedError("Label position over 7 bits is not supported yet.")

        if not self.label_manager.is_label_defined(label_name):
            raise ValueError(f"Label '{label_name}' does not exist.")
        prl = self.register_manager.prl
        if prl.mode == RegisterMode.LABEL :
            if prl.value == label_name:
                return self.__get_assembly_lines_len()
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
        expression = expression.replace('&', ' & ')
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
            return tok in ('+', '-', '&')

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

        # 3) (+/- & term)* döngüsü
        while idx < len(tokens):
            op = tokens[idx]
            if not is_op(op):
                raise ValueError(f"Expected '+' or '-' or '&', got '{op}' in '{expression}'")
            idx += 1
            if idx >= len(tokens):
                raise ValueError(f"Trailing operator '{op}' without term in '{expression}'")

            term = tokens[idx]

            if CSM.is_decimal(term):
                self.__set_reg_const(ra, CSM.convert_to_decimal(term))
                if op == '+':
                    self.__add_reg(ra)     # ACC = RD + RA
                elif op == '&':
                    self.__and_reg(ra)
                else:
                    self.__add_assembly_line(f"sub {ra.name}")  # ACC = RD - RA
                # Move ACC back to RD only if more operations follow
                if idx + 1 < len(tokens):
                    self.__add_assembly_line("mov rd, acc")
                    self.register_manager.rd.set_unknown_mode()
            else:
                if not self.var_manager.check_variable_exists(term):
                    raise ValueError(f"Unknown variable in expression: '{term}'")
                v = self.var_manager.get_variable(term)
                self.__set_marl(v)
                if op == '+':
                    self.__add_ml()        # ACC = RD + [MAR]
                elif op == '&':
                    self.__and_ml()        # ACC = RD & [MAR]
                else:
                    self.__add_assembly_line("sub ml")  # ACC = RD - [MAR]
                if idx + 1 < len(tokens):
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
        self.register_manager.acc.set_temp_var_mode(f"{rd.name} + {register.name}")
        return self.__get_assembly_lines_len()
    
    def __and_reg(self, register:Register) -> int:
        pre_assembly_lines = []
        rd = self.register_manager.rd
        self.__add_assembly_line(f"and {register.name}")
        self.register_manager.acc.set_temp_var_mode(f"{rd.name} & {register.name}")
        return self.__get_assembly_lines_len()
    
    def __add_ml(self) -> int:
        
        self.assembly_lines.append("add ml")
        return self.__get_assembly_lines_len()

    def __and_ml(self) -> int:
        self.assembly_lines.append("and ml")
        return self.__get_assembly_lines_len()

    def __compile_condition(self, condition: Condition) -> int:
        rd = self.register_manager.rd
        if condition.type is None:
            raise ValueError("Condition type is not set. Call __set_type() first.")

        left, right = condition.parts
        if not self.var_manager.check_variable_exists(left):
            raise ValueError(f"Left part of condition '{left}' is not a defined variable.")
        left_var = self.var_manager.get_variable(left)

        # Load RIGHT into RD (strict: don't rely on cached-const in RA, it may be clobbered in loop body)
        if CSM.is_decimal(right):
            self.__set_reg_const_strict(rd, CSM.convert_to_decimal(right) & 0xFF)
        else:
            if not self.var_manager.check_variable_exists(right):
                raise ValueError(f"Right part of condition '{right}' is not a defined variable.")
            right_var = self.var_manager.get_variable(right)
            self.__set_reg_variable(rd, right_var)

        # Compare RD (A) with ML (B) where ML is LEFT
        self.__set_marl(left_var)
        self.__add_assembly_line("sub ml")

        return self.__get_assembly_lines_len()

    def __set_reg_const_strict(self, reg: Register, value: int) -> int:
        """Build the 8-bit constant directly into 'reg' without reusing another cached const register.
        This prevents sequences like 'mov rd, ra' when RA was modified earlier at runtime.
        """
        value &= 0xFF
        return self.__build_const_in_reg(value, reg)
    
    @staticmethod
    def __group_line_commands(lines:list[str]) -> list[Command]:
        grouped_lines:list[Command] = []
        lindex = 0
        if isinstance(lines, str):
            lines = [lines]
        while lindex < len(lines):
            line = lines[lindex]
            logger.debug(f"Parsing line {lindex}: '{line}'")
            if VarDefCommand.match_regex(line):
                logger.debug(f"Matched VarDefCommand: '{line}'")
                grouped_lines.append(VarDefCommand(line))
                lindex += 1
            elif VarDefCommandWithoutValue.match_regex(line):
                logger.debug(f"Matched VarDefCommandWithoutValue: '{line}'")
                grouped_lines.append(VarDefCommandWithoutValue(line))
                lindex += 1
            elif StoreToDirectAddressCommand.match_regex(line):
                logger.debug(f"Matched StoreToDirectAddressCommand: '{line}'")
                grouped_lines.append(StoreToDirectAddressCommand(line))
                lindex += 1
            elif AssignCommand.match_regex(line):
                logger.debug(f"Matched AssignCommand: '{line}'")
                grouped_lines.append(AssignCommand(line))
                lindex += 1
            elif FreeCommand.match_regex(line):
                logger.debug(f"Matched FreeCommand: '{line}'")
                grouped_lines.append(FreeCommand(line))
                lindex += 1
            elif line.startswith('dasm'):
                logger.debug(f"Direct assembly block starting at line {lindex}")
                group = []
                while lindex < len(lines):
                    lindex += 1
                    if lines[lindex].startswith('endasm'):
                        break
                    group.append(lines[lindex])
                    
                lindex += 1
                grouped_lines.append(DirectAssemblyCommand(DirectAssemblyClause.parse_from_lines(group)))
            
            elif line.startswith('if '):
                logger.debug(f"If block starting at line {lindex}")
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
                logger.debug(f"Parsed if-else with {len(grouped_if_else)} sections")
                if_clause = IfElseClause.parse_from_lines(grouped_if_else)
                if_clause.apply_to_all_lines(lambda lines: Compiler.__group_line_commands(lines) if isinstance(lines, list) else Compiler.__group_line_commands([lines]))
                grouped_lines.append(Command(CommandTypes.IF, if_clause))

            elif line.startswith('while '):
                logger.debug(f"While loop starting at line {lindex}")
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
                logger.debug(f"While condition: '{cond}'")
                wc = WhileClause(cond)
                # Body is group[1:]; convert entire body into Commands, preserving nested if/else
                body = group[1:]
                body_cmds = Compiler.__group_line_commands(body)
                wc.lines = body_cmds
                grouped_lines.append(Command(CommandTypes.WHILE, wc))
                # Skip the 'endwhile'
                lindex += 1

            elif line.startswith('endif'):
                logger.debug(f"endif at line {lindex}, skipping")
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
        """Process #define directives and apply object-like macro replacements to self.lines."""
        if not self.lines:
            return
        raw_lines = self.lines
        defs: dict[str, str] = {}
        kept: list[str] = []
        def_re = re.compile(r'^\s*#define\s+([A-Za-z_][A-Za-z0-9_]*)\s+(.+?)\s*$')
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
        # Skip redundant self-moves like 'mov acc, acc'
        m = re.match(r"^\s*mov\s+([A-Za-z_][A-Za-z0-9_]*)\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*$", lines)
        if m and m.group(1) == m.group(2):
            return self.assembly_lines.__len__()

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
    # Setup logging for test execution
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
    
    compiler = create_default_compiler()
    
    compiler.load_lines('files/count_test.arn')
    compiler.break_commands()
    compiler.clean_lines()
    compiler.group_commands()
    logger.info(f"Grouped {len(compiler.grouped_lines)} commands")
    compiler.compile_lines()
    
    logger.info(f"Generated {len(compiler.assembly_lines)} assembly lines")
    for line in compiler.assembly_lines:
        print(line)


