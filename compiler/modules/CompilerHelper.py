from __future__ import annotations

import re
import logging
from dataclasses import dataclass

from VariableManager import VarTypes, Variable, ByteVariable, VarManager
from StackManager import StackManager
from LabelManager import LabelManager
from RegisterManager import RegisterManager, RegisterMode, Register
from ConditionHelper import IfElseClause, Condition, WhileClause, DirectAssemblyClause, WhileTypes, ConditionTypes
import CompilerStaticMethods as CSM
from MyEnums import ExpressionTypes
from Commands import *
from RegTags import AbsAddrTag
from ExpressionHelper import simplify_expression, plan_compilation

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
        self.arithmetic_ops = ['+', '-', '&']
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
        """Process preprocessor directives and remove comments (// style)"""
        self.__preprocess_lines()
        # Split on // for comment removal (not ; anymore)
        self.lines = [line.split(';')[0].strip() for line in self.lines 
                     if line.strip() and not line.startswith(self.comment_char)]

    def clean_lines(self) -> None:
        """Normalize whitespace in lines"""
        self.lines = [re.sub(r'\s+', ' ', line).strip() for line in self.lines 
                     if line.strip() and not line.startswith(self.comment_char)]
    
    def is_variable_defined(self, var_name: str) -> bool:
        return self.var_manager.check_variable_exists(var_name)

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
                    var_value=command.var_value,
                    volatile=command.is_volatile
                    )
        logger.warning("S:"+str(command.is_volatile))
        logger.debug(f"Created variable '{new_var.name}' of type {new_var.get_value_type()} at address 0x{new_var.address:04X} with initial value {new_var.value} (volatile:{new_var.volatile})")
        if command.var_type == VarTypes.BYTE:
            self.var_manager.set_variable_runtime_value(command.var_name, command.var_value & 0xFF)
            if new_var.volatile:
                # For volatile variables, always initialize in memory
                logger.debug(f"Variable definition: '{new_var.name}' at address 0x{new_var.address:04X} (volatile)")
                self.__set_mar_abs(new_var.address)
                self.__set_ra_const(command.var_value & 0xFF)
                self.register_manager.marl.set_variable(new_var, RegisterMode.ADDR)
                self.__store_with_current_mar_abs(new_var.address, self.register_manager.ra)
            else:
                pass
        else:
            raise ValueError(f"Unsupported variable type: {command.var_type}")
        
        return self.__get_assembly_lines_len()

    # === Unified assignment helpers ===
    def __try_evaluate_compile_time(self, expr: str) -> int | None:
        """Try to evaluate expression at compile-time if all operands are known.
        Returns value if successful, None otherwise."""
        s = expr.strip()
        
        # 1. Pure constant
        try:
            val = CSM.convert_to_decimal(s)
            if val is not None:
                return val & 0xFF
        except:
            pass
        
        # 2. Array access with known value
        m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\[(.+)\]$', s)
        if m:
            arr_name, idx_expr = m.group(1), m.group(2).strip()
            try:
                const_idx = CSM.convert_to_decimal(idx_expr)
                if const_idx is not None:
                    if self.var_manager.check_variable_exists(arr_name):
                        arr_var = self.var_manager.get_variable(arr_name)
                        if type(arr_var) == VarTypes.BYTE_ARRAY.value and not arr_var.volatile:
                            element_addr = arr_var.address + const_idx
                            runtime_val = self.var_manager.get_memory_runtime_value(element_addr)
                            if runtime_val is not None:
                                return runtime_val & 0xFF
            except:
                pass
        
        # 3. Single variable with known value
        if self.var_manager.check_variable_exists(s):
            v = self.var_manager.get_variable(s)
            if not v.volatile:
                runtime_val = self.var_manager.get_variable_runtime_value(s)
                if runtime_val is not None:
                    return runtime_val & 0xFF
        
        # 4. Complex expressions: substitute known values and evaluate
        if any(op in s for op in ['+', '-', '&', '*', '/', '<<', '>>']):
            try:
                # Substitute all known variables and array elements with their values
                substituted = self._change_expression_with_var_values(s)
                
                # Check if all operands are now constants
                tokens = self._tokenize_expression(substituted)
                all_const = True
                for t in tokens:
                    if t.strip() not in ['+', '-', '&', '*', '/', '<<', '>>']:
                        # Check if this token is a constant
                        try:
                            CSM.convert_to_decimal(t.strip())
                        except:
                            all_const = False
                            break
                
                if all_const:
                    # All operands are constants - try to evaluate
                    try:
                        # Use simplify_expression which can handle arithmetic
                        simplified = self._simplify_expression(substituted)
                        result = CSM.convert_to_decimal(simplified)
                        if result is not None:
                            logger.debug(f"Compile-time evaluation: '{s}' → '{substituted}' → {result}")
                            return result & 0xFF
                    except Exception as e:
                        logger.debug(f"Failed to evaluate '{substituted}': {e}")
            except Exception as e:
                logger.debug(f"Expression substitution failed: {e}")
        
        return None

    def __compute_rhs(self, expr: str) -> Register:
        """
        Compute RHS expression using ISA-aware ExpressionHelper.
        Returns register holding the final result (ACC for expressions, RA for constants, RD for variables).
        
        Supports:
        - Constants: 5, 0xFF, 0b1010
        - Variables: x, volatile_var
        - Arrays: arr[0], arr[idx]
        - Dereference: *0x1234
        - Expressions: a + b, x * 2, (a + b) * 3
        - ISA-aware: MUL/DIV/SHIFT → ADD expansion
        """
        s = expr.strip()
        
        # 1. Direct absolute memory dereference: *<address>
        if s.startswith('*'):
            inner = s[1:].strip()
            try:
                address = CSM.convert_to_decimal(inner)
            except Exception:
                address = None
            if address is None:
                raise ValueError(f"Invalid dereference address: {s}")
            self.__set_mar_abs(address)
            self.__ldr(self.register_manager.rd)
            return self.register_manager.rd
        
        # 2. Array access: name[idx]
        m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\[(.+)\]$', s)
        if m:
            arr_name, idx_expr = m.group(1), m.group(2).strip()
            if not self.var_manager.check_variable_exists(arr_name):
                raise ValueError(f"Array '{arr_name}' is not defined.")
            arr_var = self.var_manager.get_variable(arr_name)
            if type(arr_var) != VarTypes.BYTE_ARRAY.value:
                raise ValueError(f"'{arr_name}' is not an array.")
            
            # Try to get constant index
            try:
                const_idx = CSM.convert_to_decimal(idx_expr)
            except:
                const_idx = None
            
            # Check if we know the runtime value (non-volatile array with constant index)
            if const_idx is not None and not arr_var.volatile:
                element_addr = arr_var.address + const_idx
                runtime_val = self.var_manager.get_memory_runtime_value(element_addr)
                if runtime_val is not None:
                    logger.debug(f"Using tracked value {runtime_val} for {arr_name}[{const_idx}]")
                    self.__set_ra_const(runtime_val)
                    return self.register_manager.ra
            
            # Load from memory
            self.__set_mar_array_elem(arr_var, idx_expr)
            self.__ldr(self.register_manager.rd)
            return self.register_manager.rd

        # 3. Check for expression operators
        if any(op in s for op in ['+', '-', '&', '*', '/', '<<', '>>','|','^','(']):
            # Use ExpressionHelper for ISA-aware compilation
            try:
                # CRITICAL: First substitute all known variable values
                # This enables compile-time evaluation: (a+b)*3+10 → (10+20)*3+10 → 100
                substituted = self._change_expression_with_var_values(s)
                logger.debug(f"Expression with substituted values: '{s}' → '{substituted}'")
                
                # Then simplify the expression (may reduce to constant)
                simplified = self._simplify_expression(substituted)
                logger.debug(f"Expression simplified: '{substituted}' → '{simplified}'")
                
                # Check if simplified to a constant
                try:
                    const_val = CSM.convert_to_decimal(simplified)
                    if const_val is not None:
                        self.__set_ra_const(const_val & 0xFF)
                        return self.register_manager.ra
                except:
                    pass
                
                # Use plan_compilation for complex expressions (parentheses, mul, div, shifts)
                # This gives us ISA-aware step-by-step execution plan
                if any(op in simplified for op in ['*', '/', '<<', '>>', '(', '|', '^']):
                    steps, final_result = self._plan_expression_compilation(simplified)
                    logger.debug(f"Planned {len(steps)} compilation steps for '{simplified}'")
                    
                    # Execute each step in order
                    # Key insight: We need to track which temp vars hold which registers
                    # BUT we must load operands freshly each time because register modes change!
                    temp_locations = {}  # Map temp var names to their current register location
                    
                    for step_idx, step in enumerate(steps):
                        logger.debug(f"Executing step {step_idx+1}/{len(steps)}: {step}")
                        
                        # Helper: Load operand into target register
                        def load_operand(operand_name: str, target_reg: Register) -> Register:
                            """Load operand into target register, return the register."""
                            if operand_name.startswith('_t'):
                                # Previous temp result - it's already in a register
                                src_reg = temp_locations.get(operand_name)
                                if src_reg is None:
                                    raise ValueError(f"Temp variable {operand_name} not found!")
                                # Move to target if different
                                if src_reg.name != target_reg.name:
                                    self.__mov(target_reg, src_reg)
                                return target_reg
                            
                            elif operand_name == '_prev':
                                # Previous result in ACC
                                if target_reg.name != 'acc':
                                    self.__mov(target_reg, self.register_manager.acc)
                                return target_reg
                            
                            elif CSM.is_decimal(operand_name):
                                # Constant value
                                val = CSM.convert_to_decimal(operand_name) & 0xFF
                                self.__set_reg_const(target_reg, val)
                                return target_reg
                            
                            elif self.var_manager.check_variable_exists(operand_name):
                                # Variable - use __set_reg_variable which handles volatile/runtime
                                var = self.var_manager.get_variable(operand_name)
                                self.__set_reg_variable(target_reg, var)
                                return target_reg
                            
                            else:
                                # Fallback: try parsing as number
                                try:
                                    val = int(operand_name) & 0xFF
                                    self.__set_reg_const(target_reg, val)
                                    return target_reg
                                except:
                                    raise ValueError(f"Unknown operand: {operand_name}")
                        
                        # Load left operand into RD
                        left_reg = load_operand(step.left, self.register_manager.rd)
                        
                        # Load right operand into RA
                        right_reg = load_operand(step.right, self.register_manager.ra)
                        
                        # Execute operation (RD op RA -> ACC)
                        if step.operation == '+':
                            self.__add(right_reg)
                        elif step.operation == '-':
                            self.__sub(right_reg)
                        elif step.operation == '&':
                            self.__and(right_reg)
                        elif step.operation == '^':
                            self.__xor(right_reg)
                        elif step.operation == '|':
                            # Bitwise OR: A | B = NOT(NOT(A) AND NOT(B)) = De Morgan's Law
                            # We have RD=A, RA=B
                            # Step 1: NOT RD -> ACC
                            self.__not()  # ACC = NOT(RD)
                            self.__mov(self.register_manager.rc, self.register_manager.acc)  # Save NOT(A) in RC
                            
                            # Step 2: NOT RA -> ACC
                            self.__mov(self.register_manager.rd, self.register_manager.ra)
                            self.__not()  # ACC = NOT(RA)
                            self.__mov(self.register_manager.ra, self.register_manager.acc)  # RA = NOT(B)
                            
                            # Step 3: RC AND RA -> ACC
                            self.__mov(self.register_manager.rd, self.register_manager.rc)  # RD = NOT(A)
                            self.__and(self.register_manager.ra)  # ACC = NOT(A) AND NOT(B)
                            
                            # Step 4: NOT ACC -> ACC
                            self.__mov(self.register_manager.rd, self.register_manager.acc)
                            self.__not()  # ACC = NOT(NOT(A) AND NOT(B)) = A | B
                        elif step.operation == '*':
                            # Variable-to-variable multiplication not supported by ISA
                            # Can only do constant multiplication (expanded to repeated addition)
                            raise NotImplementedError(
                                f"Variable-to-variable multiplication not supported: {step.left} * {step.right}. "
                                f"ArniComp ISA has no hardware MUL instruction. "
                                f"Only constant multiplications like 'x * 5' are supported (expanded to repeated addition)."
                            )
                        elif step.operation == '/':
                            # Division not supported
                            raise NotImplementedError(
                                f"Division not supported: {step.left} / {step.right}. "
                                f"ArniComp ISA has no hardware DIV instruction."
                            )
                        elif step.operation in ['<<', '>>']:
                            # Shift not directly supported
                            raise NotImplementedError(
                                f"Variable shift not supported: {step.left} {step.operation} {step.right}. "
                                f"Only constant shifts are supported (expanded to multiplication/division)."
                            )
                        else:
                            raise ValueError(f"Unsupported operation in plan: {step.operation}")
                        
                        # Store result location: this step's result is now in ACC
                        temp_locations[step.result_temp] = self.register_manager.acc
                        logger.debug(f"  Result {step.result_temp} stored in ACC")
                    
                    # Final result
                    if final_result.startswith('_t'):
                        # Result is in the temp variable's register (should be ACC after last step)
                        return temp_locations[final_result]
                    elif final_result == '0':
                        self.__set_ra_const(0)
                        return self.register_manager.ra
                    else:
                        # Direct result (shouldn't happen with plan_compilation)
                        return self.register_manager.acc
                
                # Simple expression (only +, -, &): use existing evaluator
                norm = self.__normalize_expression(simplified)
                self.__evaluate_expression(norm)  # Result in ACC
                return self.register_manager.acc
            except Exception as e:
                logger.warning(f"ExpressionHelper failed: {e}, falling back to simple evaluation")
                norm = self.__normalize_expression(s)
                self.__evaluate_expression(norm)
                return self.register_manager.acc

        # 4. Pure constant
        try:
            val = CSM.convert_to_decimal(s)
            if val is not None:
                self.__set_ra_const(val & 0xFF)
                return self.register_manager.ra
        except Exception:
            pass

        # 5. Single variable
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
        
        # Dynamic index - check if runtime value is known
        if not self.var_manager.check_variable_exists(idx_s):
            raise NotImplementedError("Array index must be a constant or an existing byte variable.")
        
        idx_var = self.var_manager.get_variable(idx_s)
        runtime_idx = self.var_manager.get_variable_runtime_value(idx_s)
        
        # If runtime value is known, treat as constant
        if runtime_idx is not None:
            logger.debug(f"Using runtime value {runtime_idx} for index variable '{idx_s}'")
            address = arr_var.address + runtime_idx
            return self.__set_mar_abs(address)
        
        # Dynamic low-page index (runtime value unknown)
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
        self.__add(self.register_manager.ra)
        self.__mov(self.register_manager.marl, self.register_manager.acc)
        try:
            self.register_manager.marl.set_unknown_mode()
        except Exception:
            pass
        return self.__get_assembly_lines_len()

    def __assign_store_to_abs(self, address: int, rhs_expr: str) -> int:
        """Store expression result to absolute address. Handles MAR conflicts automatically."""
        # Compute RHS first (may use MAR internally)
        src_reg = self.__compute_rhs(rhs_expr)
        
        # CRITICAL: If src_reg is RA, we must move it to another register before setting MAR
        # because __set_mar_abs will clobber RA
        if src_reg.name == 'ra':
            self.__mov(self.register_manager.rd, src_reg)
            src_reg = self.register_manager.rd
        
        # Now set MAR to target address
        self.__set_mar_abs(address)
        
        # Store
        self.__str(src_reg)
        
        # Update runtime tracking if applicable
        if address < self.var_manager.mem_end_addr and address >= self.var_manager.mem_start_addr:
            var_in_mem = self.var_manager.get_variable_from_address(address)
            if var_in_mem is not None:
                reg_with_var = self.register_manager.check_for_variable(var_in_mem)
                if reg_with_var is not None and reg_with_var.mode == RegisterMode.VALUE:
                    reg_with_var.set_unknown_mode()
                
                # Track constant values
                try:
                    value = CSM.convert_to_decimal(rhs_expr.strip())
                    if value is not None:
                        self.var_manager.set_variable_runtime_value(var_in_mem.name, value & 0xFF)
                    else:
                        self.var_manager.invalidate_runtime_value(var_in_mem.name)
                except:
                    self.var_manager.invalidate_runtime_value(var_in_mem.name)
        
        return self.__get_assembly_lines_len()
    

    def _simplify_expression(self, expr: str) -> str:
        """
        Simplify an arithmetic expression to its most reduced form.
        
        Delegates to ExpressionHelper.simplify_expression for the actual work.
        
        Args:
            expr: Expression string to simplify
            
        Returns:
            Simplified expression string
            
        Examples:
            >>> self._simplify_expression("a + b - a")
            'b'
            >>> self._simplify_expression("2 * 3 + 4")
            '10'
        """
        return simplify_expression(expr)
    
    def _plan_expression_compilation(self, expr: str):
        """
        Plan compilation steps for expression with proper operator precedence.
        
        Returns list of steps that need to be executed in order.
        Each step is a CompilationStep with operation, left, right, result_temp.
        
        Args:
            expr: Expression string to plan
            
        Returns:
            Tuple of (steps_list, final_result_temp)
            
        Examples:
            >>> steps, result = self._plan_expression_compilation("a * b + 10")
            >>> # steps[0]: _t0 = a * b
            >>> # steps[1]: _t1 = _t0 + 10
            >>> # result: "_t1"
        """
        return plan_compilation(expr)
        
    
    def _change_expression_with_var_values(self, expr: str) -> str:
        """Replace variables and array accesses with their compile-time known values.
        
        Uses ExpressionHelper's tokenizer to properly handle all operators and parentheses.
        
        Examples:
            'a + b + 30' → '10 + 20 + 30' (if a=10, b=20)
            '(a+b)*3' → '(10+20)*3' (if a=10, b=20)
            'data[0] + data[1]' → '10 + 20' (if data[0]=10, data[1]=20)
        """
        # Import tokenizer from ExpressionHelper
        from ExpressionHelper import ExpressionTokenizer
        
        # Use proper tokenizer that handles all operators and parentheses
        tokens = ExpressionTokenizer.tokenize(expr)
        new_tokens = []
        
        for t in tokens:
            t_stripped = t.strip()
            
            # Skip operators and parentheses
            if t_stripped in ['+', '-', '*', '/', '&', '|', '^', '<<', '>>', '(', ')']:
                new_tokens.append(t_stripped)
                continue
            
            # Check for array access: name[idx]
            # Note: ExpressionTokenizer doesn't split arr[idx], it keeps it as one token
            m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\[(.+)\]$', t_stripped)
            if m:
                arr_name, idx_expr = m.group(1), m.group(2).strip()
                # Try to get constant index and tracked value
                try:
                    const_idx = CSM.convert_to_decimal(idx_expr)
                    if const_idx is not None and self.var_manager.check_variable_exists(arr_name):
                        arr_var = self.var_manager.get_variable(arr_name)
                        if type(arr_var) == VarTypes.BYTE_ARRAY.value and not arr_var.volatile:
                            element_addr = arr_var.address + const_idx
                            runtime_val = self.var_manager.get_memory_runtime_value(element_addr)
                            if runtime_val is not None:
                                new_tokens.append(str(runtime_val))
                                logger.debug(f"Substituted {arr_name}[{const_idx}] with {runtime_val}")
                                continue
                except:
                    pass
                # If we couldn't substitute, keep original
                new_tokens.append(t)
                continue
            
            # Check for simple variable
            if self.var_manager.check_variable_exists(t_stripped):
                v = self.var_manager.get_variable(t_stripped)
                if not v.volatile:
                    rt_val = self.var_manager.get_variable_runtime_value(t_stripped)
                    if rt_val is not None:
                        new_tokens.append(str(rt_val))
                        logger.debug(f"Substituted variable '{t_stripped}' with {rt_val}")
                        continue
            
            # Keep token as-is (constant or unknown variable)
            new_tokens.append(t)
        
        # Reconstruct expression with proper spacing
        new_expr = ' '.join(new_tokens)
        logger.debug(f"Expression value substitution: '{expr}' → '{new_expr}'")
        return new_expr
    
    def _tokenize_expression(self, expr:str) -> list[str]:
        """Tokenize expression into variables/constants and operators.
        Handles array access syntax: arr[idx]"""
        tokens = []
        current = ''
        bracket_depth = 0
        
        for char in expr:
            if char == '[':
                bracket_depth += 1
                current += char
            elif char == ']':
                bracket_depth -= 1
                current += char
            elif char in self.arithmetic_ops and bracket_depth == 0:
                if current:
                    tokens.append(current.strip())
                    current = ''
                tokens.append(char)
            else:
                current += char
        
        if current:
            tokens.append(current.strip())
        return tokens


    def __compile_assign_var(self, var: Variable, rhs_expr: str) -> int:
        """var = expr; Optimizes by skipping memory writes when value is compile-time known and not volatile."""

        if type(var) is VarTypes.BYTE.value:
            # Check for "var = var + x" pattern (ADDI optimization)
            import re
            addi_pattern = rf'^{re.escape(var.name)}\s*\+\s*(0x[0-9A-Fa-f]+|0b[01]+|\d+)$'
            m = re.match(addi_pattern, rhs_expr.strip())
            if m:
                imm_text = m.group(1)
                try:
                    imm = int(imm_text, 0)  # base=0 allows 0x and 0b
                except ValueError:
                    imm = None

                if imm is not None and imm > 0:
                    logger.debug(f"ADDI optimization attempt: {var.name} = {var.name} + {imm}")

                    prev_value = self.var_manager.get_variable_runtime_value(var.name)

                    # If imm fits in 3-bit immediate (1..7), emit single addi #imm
                    if var.volatile or prev_value is None:
                        # must load from memory then add immediate and store
                        self.__set_mar_abs(var.address)
                        self.__ldr(self.register_manager.rd)
                        self.__addi(imm)
                        self.__str(self.register_manager.acc)
                        # runtime value unknown (we loaded from memory), invalidate tracking
                        self.var_manager.invalidate_runtime_value(var.name)
                    else:
                        # we know runtime value and variable not volatile -> update tracking only
                        new_value = (prev_value + imm) & 0xFF
                        self.var_manager.set_variable_runtime_value(var.name, new_value)
                        logger.debug(f"Compile-time only: {var.name} = {new_value} (no memory write)")
                        return self.__get_assembly_lines_len()

                    return self.__get_assembly_lines_len()
            
            # Try to evaluate RHS at compile-time
            rhs_value = self.__try_evaluate_compile_time(rhs_expr)
            
            # Optimization: If variable is not volatile and we have a compile-time constant,
            # just track it without generating code
            if not var.volatile and rhs_value is not None:
                self.var_manager.set_variable_runtime_value(var.name, rhs_value & 0xFF)
                logger.debug(f"Compile-time only: {var.name} = {rhs_value & 0xFF} (no memory write)")
                return self.__get_assembly_lines_len()
            
            # Normal code generation path
            # Compute RHS first (handles MAR internally)
            src_reg = self.__compute_rhs(rhs_expr)
            
            # CRITICAL: If src_reg is RA, we must move it to another register before setting MAR
            # because __set_mar_abs will clobber RA
            if src_reg.name == 'ra':
                self.__mov(self.register_manager.rd, src_reg)
                src_reg = self.register_manager.rd
            
            # Set MAR to target variable
            self.__set_mar_abs(var.address)
            
            # Store
            self.__str(src_reg)
            
            # Try to track runtime value
            try:
                if rhs_value is not None:
                    self.var_manager.set_variable_runtime_value(var.name, rhs_value & 0xFF)
                else:
                    self.var_manager.invalidate_runtime_value(var.name)
            except:
                self.var_manager.invalidate_runtime_value(var.name)
            
            return self.__get_assembly_lines_len()
        elif type(var) is VarTypes.UINT16.value:
            # Compute RHS first
            src_reg = self.__compute_rhs(rhs_expr)
            
            # Set MAR and store
            self.__set_mar_abs(var.address)
            self.__str(src_reg)
            return self.__get_assembly_lines_len()
        elif type(var) is VarTypes.UINT16.value:
            exp_type = CSM.get_expression_type(rhs_expr)
            if exp_type == ExpressionTypes.SINGLE_DEC or exp_type == ExpressionTypes.ALL_DEC:

                if exp_type == ExpressionTypes.SINGLE_DEC:
                    rhs_dec = CSM.convert_to_decimal(rhs_expr)    
                elif exp_type == ExpressionTypes.ALL_DEC:     
                    rhs_dec = eval(rhs_expr)

                if rhs_dec is None or not isinstance(rhs_dec, int):
                    raise ValueError("Invalid UINT16 value.")

                rhs_byte_count = CSM.get_decimal_byte_count(rhs_dec)
                if rhs_byte_count > 2:
                    raise ValueError("UINT16 value out of range (0-65535).")
                
                rhs_bytes = CSM.get_decimal_bytes(rhs_dec)
                logger.debug(f"Variable definition: {var.name} at address 0x{var.address:04X}")
                self.__set_mar_abs(var.address)
                self.__set_ra_const(rhs_bytes[0])
                self.__str(self.register_manager.ra)

                self.__set_mar_abs(var.address+1)
                self.__set_ra_const(rhs_bytes[1])
                self.__str(self.register_manager.ra)
                
                return self.__get_assembly_lines_len()
                
            else:
                raise NotImplementedError("UINT16 assignment only supports direct literals for now.")
            
        else:
            raise ValueError(f"Unsupported variable type for assignment: {type(var)}")


    def __compile_assign_array(self, arr_var: Variable, index_expr: str, rhs_expr: str) -> int:
        """arr[idx] = expr; Optimizes by skipping memory writes when value is compile-time known and not volatile.
        Tracks array element runtime values for constant indices."""
        
        # Try to get constant index for tracking
        try:
            const_idx = CSM.convert_to_decimal(index_expr.strip())
        except:
            const_idx = None
        
        # Try to evaluate RHS at compile-time
        rhs_value = self.__try_evaluate_compile_time(rhs_expr)
        
        # Optimization: If array is not volatile, index is constant, and RHS is compile-time known,
        # just track it without generating code
        if const_idx is not None and not arr_var.volatile and rhs_value is not None:
            element_addr = arr_var.address + const_idx
            self.var_manager.set_memory_runtime_value(element_addr, rhs_value & 0xFF)
            logger.debug(f"Compile-time only: {arr_var.name}[{const_idx}] = {rhs_value & 0xFF} (no memory write)")
            return self.__get_assembly_lines_len()
        
        # Normal code generation path
        # Compute RHS first (may use MAR)
        src_reg = self.__compute_rhs(rhs_expr)
        
        # CRITICAL: If src_reg is RA, we must move it to another register before setting MAR
        # because __set_mar_array_elem may clobber RA
        if src_reg.name == 'ra':
            self.__mov(self.register_manager.rd, src_reg)
            src_reg = self.register_manager.rd
        
        # Now set MAR to array element
        self.__set_mar_array_elem(arr_var, index_expr)
        
        # Store
        self.__str(src_reg)
        
        # Track runtime value for non-volatile arrays with constant index
        if const_idx is not None and not arr_var.volatile:
            element_addr = arr_var.address + const_idx
            try:
                if rhs_value is not None:
                    self.var_manager.set_memory_runtime_value(element_addr, rhs_value & 0xFF)
                    logger.debug(f"Tracked array element: {arr_var.name}[{const_idx}] = {rhs_value & 0xFF} (addr 0x{element_addr:04X})")
                else:
                    self.var_manager.invalidate_memory_runtime_value(element_addr)
            except:
                self.var_manager.invalidate_memory_runtime_value(element_addr)
        
        return self.__get_assembly_lines_len()

    def __create_var(self, command: VarDefCommandWithoutValue) -> int:
        """Create variable without initial value. Supports volatile arrays."""
        if command.var_type == VarTypes.BYTE_ARRAY:
            if command.array_length is None:
                raise ValueError("Array length must be specified for BYTE_ARRAY.")
            new_var: Variable = self.var_manager.create_array_variable(
                var_name=command.var_name, 
                var_type=command.var_type, 
                array_len=command.array_length, 
                var_value=[0] * command.array_length,
                volatile=command.is_volatile
            )
            logger.debug(f"Created array '{new_var.name}' of size {command.array_length} at address 0x{new_var.address:04X} (volatile:{command.is_volatile})")
        else:
            new_var: Variable = self.var_manager.create_variable(
                var_name=command.var_name, 
                var_type=command.var_type, 
                var_value=0,
                volatile=command.is_volatile
            )
            # DON'T track runtime value for uninitialized variables - value is unknown!
            # Only explicit initializations (VarDefCommand) should track values
            logger.debug(f"Created variable '{new_var.name}' at address 0x{new_var.address:04X} (volatile:{command.is_volatile}) [uninitialized]")
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

    def __set_mar_abs(self, address: int) -> int:
        """Set MAR to an absolute address with INX optimization. Keeps register cache tags."""
        marl = self.register_manager.marl
        marh = self.register_manager.marh
        ra = self.register_manager.ra
        low = address & 0xFF
        high = (address >> 8) & 0xFF

        current_low = marl.tag.addr & 0xFF if marl.tag is not None and isinstance(marl.tag, AbsAddrTag) else None
        current_high = marh.tag.addr & 0xFF if marh.tag is not None and isinstance(marh.tag, AbsAddrTag) else None
        
        if current_low == None or current_low != low:
            # MARL needs to be changed
            if current_low is not None:
                logger.debug(f"Current MARL is 0x{current_low:02X}, needs to change to 0x{low:02X}")
                inx_steps = CSM.inc_steps_to_target(current_low, low)
                if inx_steps <= 2:
                    logger.debug(f"Using {inx_steps}x INX to reach 0x{low:02X}")
                    for _ in range(inx_steps):
                        self.__inx()
                    marl.tag = AbsAddrTag(low)
                else:
                    logger.debug(f"Using LDI to set MARL to 0x{low:02X} (more efficient than {inx_steps}x INX)")
                    self.__build_const_in_reg(low, marl)
                    marl.tag = AbsAddrTag(low)
            else:
                logger.debug(f"MARL is not known, updating to 0x{low:02X} (MAR=0x{address:04X})")
                self.__build_const_in_reg(low, marl)
                marl.tag = AbsAddrTag(low)
            
        else:
            logger.debug(f"MARL already set to 0x{low:02X}")
        
        if current_high == None or current_high != high:
            # MARH needs to be changed
            if current_high is not None:
                logger.debug(f"Current MARH is 0x{current_high:02X}, needs to change to 0x{high:02X}")
                self.__build_const_in_reg(high, marh)
                marh.tag = AbsAddrTag(high)
            else:
                logger.debug(f"MARH is not known, updating to 0x{high:02X} (MAR=0x{address:04X})")
                self.__build_const_in_reg(high, marh)
                marh.tag = AbsAddrTag(high)
            pass
        else:
            logger.debug(f"MARH already set to 0x{high:02X}")
        
        return self.__get_assembly_lines_len()

## LOW LEVEL ASSEMBLY HELPERS
    def __ldi(self, value: int) -> int:
        """LDI instruction: RA <- immediate (0-127). Updates RA register state."""
        if value > MAX_LDI:
            raise ValueError(f"Value {value} exceeds maximum LDI value of {MAX_LDI}.")
        self.__add_assembly_line(f"ldi #{value}")
        self.register_manager.ra.set_mode(RegisterMode.CONST, value)
        return self.__get_assembly_lines_len()
    
    def __inx(self) -> int:
        """INX instruction: MARL <- MARL + 1 (wraps at 0xFF). Updates MARL tag if tracked."""
        self.__add_assembly_line("inx")
        marl = self.register_manager.marl
        
        # Update MARL tag if it exists
        if marl.tag is not None and isinstance(marl.tag, AbsAddrTag):
            old_addr = marl.tag.addr
            # Increment low byte, wrapping at 0xFF
            new_low = (old_addr + 1) & 0xFF 
            if new_low > MAX_LOW_ADDRESS:
                raise ValueError("INX would overflow into high page, which is unsupported.")
        
            marl.tag = AbsAddrTag(new_low)
            logger.debug(f"INX: MARL 0x{old_addr:02X} -> 0x{new_low:02X}")
        else:
            # If no tag, invalidate mode
            try:
                marl.set_unknown_mode()
            except Exception:
                pass
        
        return self.__get_assembly_lines_len()
    
    def __addi(self, value: int) -> int:
        """ADDI instruction: ACC <- RD + immediate (1-7). Tracks result if RD is known."""
        if not (1 <= value <= 7):
            raise ValueError(f"ADDI immediate must be in range 1-7, got {value}")
        
        self.__add_assembly_line(f"addi #{value}")
        
        rd = self.register_manager.rd
        acc = self.register_manager.acc
        
        # Try to compute constant result if RD is known
        if rd.mode == RegisterMode.CONST:
            new_val = (rd.value + value) & 0xFF
            acc.set_mode(RegisterMode.CONST, new_val)
        else:
            acc.set_unknown_mode()
        
        return self.__get_assembly_lines_len()
    
    def __ldr(self, dst: Register) -> int:
        """Load from memory at MAR into dst register. Uses MOV dst, M. Result is unknown."""
        self.__add_assembly_line(f"mov {dst.name}, m")
        dst.set_unknown_mode()
        return self.__get_assembly_lines_len()
    
    def __str(self, src: Register) -> int:
        """Store src register to memory at MAR. Uses MOV M, src."""
        self.__add_assembly_line(f"mov m, {src.name}")
        return self.__get_assembly_lines_len()
    
    def __mov(self, dst: Register, src: Register) -> int:
        """MOV instruction: dst <- src. Tracks register state propagation."""
        if dst.name == src.name:
            return self.__get_assembly_lines_len()
        if not src.outable:
            raise ValueError(f"Source register {src.name} is not outable.")
        if not dst.writable:
            raise ValueError(f"Destination register {dst.name} is not writable.")
        
        self.__add_assembly_line(f"mov {dst.name}, {src.name}")
        
        # Propagate register state
        if src.mode == RegisterMode.UNKNOWN:
            dst.set_unknown_mode()
        elif src.mode == RegisterMode.CONST:
            dst.set_mode(RegisterMode.CONST, src.value)
        elif src.mode == RegisterMode.VALUE and src.variable is not None:
            # Propagate variable binding
            dst.set_variable(src.variable, RegisterMode.VALUE)
        elif src.mode == RegisterMode.ADDR and src.variable is not None:
            # Propagate address binding
            dst.set_variable(src.variable, RegisterMode.ADDR)
        else:
            # Unknown mode or unsupported state
            dst.set_unknown_mode()
        return self.__get_assembly_lines_len()
    
    def __add(self, src: Register) -> int:
        """ADD instruction: ACC <- RD + src. Tracks result in ACC."""
        self.__add_assembly_line(f"add {src.name}")
        
        acc = self.register_manager.acc
        rd = self.register_manager.rd
        
        # Try to compute constant result if both are known
        if rd.mode == RegisterMode.CONST and src.mode == RegisterMode.CONST:
            result = (rd.value + src.value) & 0xFF
            acc.set_mode(RegisterMode.CONST, result)
        else:
            acc.set_unknown_mode()
        
        return self.__get_assembly_lines_len()
    
    def __sub(self, src: Register) -> int:
        """SUB instruction: ACC <- RD - src. Tracks result in ACC."""
        self.__add_assembly_line(f"sub {src.name}")
        
        acc = self.register_manager.acc
        rd = self.register_manager.rd
        
        # Try to compute constant result if both are known
        if rd.mode == RegisterMode.CONST and src.mode == RegisterMode.CONST:
            result = (rd.value - src.value) & 0xFF
            acc.set_mode(RegisterMode.CONST, result)
        else:
            acc.set_unknown_mode()
        
        return self.__get_assembly_lines_len()
    
    def __and(self, src: Register) -> int:
        """AND instruction: ACC <- RD & src. Tracks result in ACC."""
        self.__add_assembly_line(f"and {src.name}")
        
        acc = self.register_manager.acc
        rd = self.register_manager.rd
        
        # Try to compute constant result if both are known
        if rd.mode == RegisterMode.CONST and src.mode == RegisterMode.CONST:
            result = (rd.value & src.value) & 0xFF
            acc.set_mode(RegisterMode.CONST, result)
        else:
            acc.set_unknown_mode()
        
        return self.__get_assembly_lines_len()
    
    def __xor(self, src: Register) -> int:
        """XOR instruction: ACC <- RD ^ src. Tracks result in ACC."""
        self.__add_assembly_line(f"xor {src.name}")
        
        acc = self.register_manager.acc
        rd = self.register_manager.rd
        
        # Try to compute constant result if both are known
        if rd.mode == RegisterMode.CONST and src.mode == RegisterMode.CONST:
            result = (rd.value ^ src.value) & 0xFF
            acc.set_mode(RegisterMode.CONST, result)
        else:
            acc.set_unknown_mode()
        
        return self.__get_assembly_lines_len()
    
    def __not(self, src: Register) -> int:
        """NOT instruction: ACC <- ~src. Tracks result in ACC."""
        self.__add_assembly_line(f"not {src.name}")
        
        acc = self.register_manager.acc
        
        # Try to compute constant result if source is known
        if src.mode == RegisterMode.CONST:
            result = (~src.value) & 0xFF
            acc.set_mode(RegisterMode.CONST, result)
        else:
            acc.set_unknown_mode()
        
        return self.__get_assembly_lines_len()
    
    def __cmp(self, src: Register) -> int:
        """CMP instruction: Compare RD with src, sets flags. Note: src must be RA, M, or ACC."""
        # CMP has restrictions: only RA, M, ACC allowed
        if src.name not in ['ra', 'm', 'acc']:
            raise ValueError(f"CMP only supports RA, M, ACC as source, got {src.name}")
        
        self.__add_assembly_line(f"cmp {src.name}")
        # CMP doesn't modify registers, only sets flags
        return self.__get_assembly_lines_len()
    
    def __subi(self, value: int) -> int:
        """SUBI instruction: ACC <- ACC - immediate (0-7)."""
        if not (0 <= value <= 7):
            raise ValueError(f"SUBI immediate must be in range 0-7, got {value}")
        
        self.__add_assembly_line(f"subi #{value}")
        
        acc = self.register_manager.acc
        
        # Try to compute constant result if ACC is known
        if acc.mode == RegisterMode.CONST:
            result = (acc.value - value) & 0xFF
            acc.set_mode(RegisterMode.CONST, result)
        else:
            acc.set_unknown_mode()
        
        return self.__get_assembly_lines_len()
    
    def __adc(self, src: Register) -> int:
        """ADC instruction: ACC <- RD + src + carry. Result unknown (carry flag not tracked)."""
        self.__add_assembly_line(f"adc {src.name}")
        self.register_manager.acc.set_unknown_mode()
        return self.__get_assembly_lines_len()
    
    def __sbc(self, src: Register) -> int:
        """SBC instruction: ACC <- RD - src - carry. Result unknown (carry flag not tracked)."""
        self.__add_assembly_line(f"sbc {src.name}")
        self.register_manager.acc.set_unknown_mode()
        return self.__get_assembly_lines_len()
    
    def __nop(self) -> int:
        """NOP instruction: No operation."""
        self.__add_assembly_line("nop")
        return self.__get_assembly_lines_len()
    
    def __hlt(self) -> int:
        """HLT instruction: Halt processor."""
        self.__add_assembly_line("hlt")
        return self.__get_assembly_lines_len()
    
    def __jmp(self) -> int:
        """JMP instruction: Unconditional jump to address in PRL."""
        self.__add_assembly_line("jmp")
        return self.__get_assembly_lines_len()
## END LOW LEVEL ASSEMBLY HELPERS

    def __set_msb_ra(self) -> int:
        self.__add_assembly_line("smsbra")
        if self.register_manager.ra.mode == RegisterMode.CONST:
            new_val = self.register_manager.ra.value | 0x80
            self.register_manager.ra.set_mode(RegisterMode.CONST, new_val)
        else:
            self.register_manager.ra.set_unknown_mode()
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
            if target_reg.name != ra.name:
                self.__mov(target_reg, ra)
            return self.__get_assembly_lines_len()

        value_except_msb = value & 0x7F  # lower 7 bits
        self.__ldi(value_except_msb)  # RA <- lower 7 bits
        self.__set_msb_ra()  # RA <- RA | 0x80
        if target_reg.name != ra.name:
            self.__mov(target_reg, ra)
        return self.__get_assembly_lines_len()

    def __store_with_current_mar_abs(self, address: int, src: Register) -> int:
        """Store src to memory at address. Assumes MAR is already set to this address."""
        marl = self.register_manager.marl
        marh = self.register_manager.marh
        low = address & 0xFF
        high = (address >> 8) & 0xFF
        logger.debug(f"MARL currently at 0x{marl.tag.addr:02X}" if marl.tag else "MAR tag unknown")
        logger.debug(f"MARH currently at 0x{marh.tag.addr:02X}" if marh.tag else "MAR tag unknown")
        logger.debug(f"Storing to address 0x{address:04X} from {src.name}")
        
        # Verify MAR tag matches expected address
        if marl.tag is not None and isinstance(marl.tag, AbsAddrTag) and marh.tag is not None and isinstance(marh.tag, AbsAddrTag):
            if marl.tag.addr != low or marh.tag.addr != high:
                raise ValueError(f"MAR does not match target address 0x{address:04X} (MAR=0x{(marh.tag.addr<<8)|marl.tag.addr:04X})")
        
        self.__str(src)
        return self.__get_assembly_lines_len()

    def __load_var_to_reg(self, var: Variable, dst: Register) -> int:
        self.__set_mar_abs(var.address)
        self.__ldr(dst)
        dst.set_variable(var, RegisterMode.VALUE)
        return self.__get_assembly_lines_len()

    def __set_ra_const(self, value:int) -> int:
        ra = self.register_manager.ra
        self.__build_const_in_reg(value, ra)
        return self.__get_assembly_lines_len()
 
    def __set_reg_variable(self, reg: Register, variable: Variable) -> int:
        """Load variable into register. Uses runtime value if known and variable is not volatile."""
        
        # Check if variable is volatile - must always read from memory
        if variable.volatile:
            self.__load_var_to_reg(variable, reg)
            return self.__get_assembly_lines_len()
        
        # Check if variable has known runtime value
        runtime_val = self.var_manager.get_variable_runtime_value(variable.name)
        if runtime_val is not None:
            # Use compile-time known value directly
            logger.debug(f"Using runtime value {runtime_val} for variable '{variable.name}'")
            self.__set_reg_const(reg, runtime_val)
            return self.__get_assembly_lines_len()
        
        # Check if variable is already in a register
        reg_with_var: Register = self.register_manager.check_for_variable(variable)
        if reg_with_var is not None:
            if reg_with_var.name == reg.name:
                return self.__get_assembly_lines_len()
            self.__mov(reg, reg_with_var)
            return self.__get_assembly_lines_len()
        
        # Fall back to memory load
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
        
        # Try to evaluate condition at compile-time
        first_condition = if_else_clause.get_if().condition
        compile_time_condition = self.__try_evaluate_condition_compile_time(first_condition)
        
        logger.debug(f"IF-ELSE compile-time condition evaluation: {compile_time_condition}")

        # Case 1: simple IF without else/elif
        if (not is_contains_else) and (not is_contains_elif):
            # If condition is compile-time known, we can optimize
            if compile_time_condition is not None:
                if compile_time_condition:
                    # Condition is TRUE: only compile IF body
                    logger.debug("Compile-time: IF branch will execute, skipping condition check")
                    if_comp = self.create_context_compiler()
                    if_comp.grouped_lines = if_else_clause.get_if().get_lines()
                    if_comp.compile_lines()
                    self.__add_assembly_line(if_comp.assembly_lines)
                    # Runtime values from IF branch are preserved
                    return self.__get_assembly_lines_len()
                else:
                    # Condition is FALSE: skip entire IF (no code generated)
                    logger.debug("Compile-time: IF condition is false, skipping entire block")
                    return self.__get_assembly_lines_len()
            
            # Runtime condition: generate normal IF with jump
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
            
            # CRITICAL: Invalidate runtime values for all variables modified in IF body
            self.__invalidate_modified_variables(if_comp.grouped_lines)
            
            self.label_manager.update_label_position(skip_label, self.__get_assembly_lines_len())
            self.__add_assembly_line(f"{skip_label}:")
            return self.__get_assembly_lines_len()

        # Case 2: IF with optional ELIFs and optional ELSE
        # Check if we can evaluate at compile-time
        if compile_time_condition is not None:
            # Compile-time known: find which branch to execute
            if compile_time_condition:
                # IF branch executes
                logger.debug("Compile-time: IF branch will execute (skipping ELIF/ELSE)")
                if_comp = self.create_context_compiler()
                if_comp.grouped_lines = if_else_clause.get_if().get_lines()
                if_comp.compile_lines()
                self.__add_assembly_line(if_comp.assembly_lines)
                return self.__get_assembly_lines_len()
            else:
                # Check ELIF conditions
                for elif_clause in if_else_clause.get_elif():
                    elif_condition_result = self.__try_evaluate_condition_compile_time(elif_clause.condition)
                    if elif_condition_result is not None and elif_condition_result:
                        logger.debug(f"Compile-time: ELIF branch will execute")
                        elif_comp = self.create_context_compiler()
                        elif_comp.grouped_lines = elif_clause.get_lines()
                        elif_comp.compile_lines()
                        self.__add_assembly_line(elif_comp.assembly_lines)
                        return self.__get_assembly_lines_len()
                
                # No ELIF matched, check ELSE
                if is_contains_else:
                    logger.debug("Compile-time: ELSE branch will execute")
                    else_comp = self.create_context_compiler()
                    else_comp.grouped_lines = if_else_clause.get_else().get_lines()
                    else_comp.compile_lines()
                    self.__add_assembly_line(else_comp.assembly_lines)
                    return self.__get_assembly_lines_len()
                else:
                    # No branch executes
                    logger.debug("Compile-time: No branch executes")
                    return self.__get_assembly_lines_len()
        
        # Runtime branching: compile all branches and invalidate modified variables
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

        # Collect all variables modified in any branch
        all_modified_vars = set()
        for _, comp in branches:
            all_modified_vars.update(self.__get_modified_variables(comp.grouped_lines))
        if else_comp is not None:
            all_modified_vars.update(self.__get_modified_variables(else_comp.grouped_lines))
        
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
            self.__jmp()

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
        
        # CRITICAL: Invalidate all variables that were modified in any branch
        for var_name in all_modified_vars:
            if self.var_manager.check_variable_exists(var_name):
                self.var_manager.invalidate_runtime_value(var_name)
                logger.debug(f"Invalidated runtime value for '{var_name}' (modified in if-else branch)")
        
        return self.__get_assembly_lines_len()

    def __handle_while(self, command: Command) -> int:
        if not isinstance(command.line, WhileClause):
            raise ValueError("Command line must be a WhileClause instance.")
        while_clause: WhileClause = command.line
        logger.debug(f"Processing while loop: type={while_clause.type}, condition='{while_clause.condition}'")
        if while_clause.type == WhileTypes.BYPASS:
            return self.__get_assembly_lines_len()
        elif while_clause.type == WhileTypes.CONDITIONAL:
            # Try compile-time evaluation
            cond_result = self.__try_evaluate_condition_compile_time(while_clause.condition)
            
            if cond_result is False:
                # Condition is always false -> skip entire loop
                logger.debug(f"While loop condition always FALSE at compile-time, skipping loop body")
                
                # Invalidate all variables modified in loop body (they won't execute, but for safety)
                modified_vars = self.__get_modified_variables(while_clause.get_lines())
                for var_name in modified_vars:
                    if var_name in self.var_manager.variables:
                        self.var_manager.invalidate_runtime_value(var_name)
                        logger.debug(f"Variable '{var_name}' invalidated (skipped loop)")
                
                return self.__get_assembly_lines_len()
            
            elif cond_result is True:
                # Condition is always true -> infinite loop (no condition check needed)
                logger.debug(f"While loop condition always TRUE at compile-time, converting to infinite loop")
                
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
                
                # Invalidate all runtime values when entering infinite loop
                for var_name in self.var_manager.variables.keys():
                    if self.var_manager.get_variable_runtime_value(var_name) is not None:
                        self.var_manager.invalidate_runtime_value(var_name)
                        logger.debug(f"Invalidated '{var_name}' runtime value (entering infinite loop)")
                
                body_comp.compile_lines()
                
                self.__add_assembly_line(body_comp.assembly_lines)
                self.__set_prl_as_label(start_label_name, self.label_manager.get_label(start_label_name))
                self.__jmp()
                return self.__get_assembly_lines_len()
            
            # Runtime condition - normal while loop
            start_label_name, _ = self.label_manager.create_while_start_label(self.__get_assembly_lines_len())
            self.__add_assembly_line(f"{start_label_name}:")
            self.__compile_condition(while_clause.condition)

            body_comp = self.create_context_compiler()
            body_comp.grouped_lines = while_clause.get_lines()
            
            # Track which variables are modified in the loop
            modified_vars = self.__get_modified_variables(while_clause.get_lines())
            
            # Invalidate all variables before entering loop (they may be read/written in loop)
            for var_name in self.var_manager.variables.keys():
                if self.var_manager.get_variable_runtime_value(var_name) is not None:
                    self.var_manager.invalidate_runtime_value(var_name)
                    logger.debug(f"Invalidated '{var_name}' runtime value (entering loop)")
            
            body_comp.compile_lines()
            body_len = body_comp.__get_assembly_lines_len()

            end_label, _ = self.label_manager.create_while_end_label(self.__get_assembly_lines_len() + body_len + 3)
            self.__set_prl_as_label(end_label, self.label_manager.get_label(end_label))
            self.__add_assembly_line(CSM.get_inverted_jump_str(while_clause.condition.type))

            self.__add_assembly_line(body_comp.assembly_lines)
            self.register_manager.set_changed_registers_as_unknown()

            self.__set_prl_as_label(start_label_name, self.label_manager.get_label(start_label_name))
            self.__jmp()

            self.label_manager.update_label_position(end_label, self.__get_assembly_lines_len())
            self.__add_assembly_line(f"{end_label}:")
            
            # After loop completes, invalidate all modified variables (unknown iteration count)
            for var_name in modified_vars:
                if var_name in self.var_manager.variables:
                    self.var_manager.invalidate_runtime_value(var_name)
                    logger.debug(f"Variable '{var_name}' invalidated after while loop (modified in loop)")
            
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
            
            for var_name in self.var_manager.variables.keys():
                if self.var_manager.get_variable_runtime_value(var_name) is not None:
                    self.var_manager.invalidate_runtime_value(var_name)
                    logger.debug(f"Invalidated '{var_name}' runtime value (entering infinite loop)")
            
            body_comp.compile_lines()
            body_len = body_comp.__get_assembly_lines_len()
            
            self.__add_assembly_line(body_comp.assembly_lines)
            self.__set_prl_as_label(start_label_name, self.label_manager.get_label(start_label_name))
            self.__jmp()
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

        # 2) Load first term into RD
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
            
            # Use __set_reg_variable which handles volatile and runtime values
            self.__set_reg_variable(rd, var0)

        idx += 1

        # 3) Process (+/- & term)* chain
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
                    self.__add(ra)     # ACC = RD + RA
                elif op == '&':
                    self.__and(ra)     # ACC = RD & RA
                else:
                    self.__sub(ra)     # ACC = RD - RA
                # Move ACC back to RD only if more operations follow
                if idx + 1 < len(tokens):
                    self.__mov(rd, acc)
            else:
                if not self.var_manager.check_variable_exists(term):
                    raise ValueError(f"Unknown variable in expression: '{term}'")
                v = self.var_manager.get_variable(term)
                
                # Check if we know the runtime value
                runtime_val = self.var_manager.get_variable_runtime_value(v.name) if not v.volatile else None
                
                if runtime_val is not None:
                    # Use known constant value
                    self.__set_reg_const(ra, runtime_val)
                    if op == '+':
                        self.__add(ra)
                    elif op == '&':
                        self.__and(ra)
                    else:
                        self.__sub(ra)
                elif v.volatile:
                    # Volatile: must read from memory
                    self.__set_mar_abs(v.address)
                    if op == '+':
                        self.__add_assembly_line("add m")  # ACC = RD + [MAR]
                    elif op == '&':
                        self.__add_assembly_line("and m")  # ACC = RD & [MAR]
                    else:
                        self.__add_assembly_line("sub m")  # ACC = RD - [MAR]
                    acc.set_unknown_mode()
                else:
                    # Non-volatile, runtime unknown: read from memory
                    self.__set_mar_abs(v.address)
                    if op == '+':
                        self.__add_assembly_line("add m")  # ACC = RD + [MAR]
                    elif op == '&':
                        self.__add_assembly_line("and m")  # ACC = RD & [MAR]
                    else:
                        self.__add_assembly_line("sub m")  # ACC = RD - [MAR]
                    acc.set_unknown_mode()
                
                if idx + 1 < len(tokens):
                    self.__mov(rd, acc)

            idx += 1

        # 5) Mark ACC as holding the expression result
        self.register_manager.acc.set_temp_var_mode(expr)

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
        # Compare RD (A) with M (B) where M is LEFT
        # Set MAR to point to left variable, then compare RD with memory at MAR
        marl = self.register_manager.marl
        marh = self.register_manager.marh
        logger.debug(f"[XXXX] CURRENT MAR {marh.tag.addr:<02X} {marl.tag.addr:<02X} TARGET VAR '{left_var.name}' ADDR {left_var.address:04X}")
        self.__set_mar_abs(left_var.address)
        # CMP instruction syntax: cmp m (where m is the value at current MAR address)
        self.__add_assembly_line("cmp m")

        return self.__get_assembly_lines_len()
    
    def __try_evaluate_condition_compile_time(self, condition: Condition) -> bool | None:
        """Try to evaluate condition at compile-time. Returns True/False if known, None if runtime-dependent."""
        try:
            left, right = condition.parts
            
            # Get left value (variable)
            if not self.var_manager.check_variable_exists(left):
                return None
            left_var = self.var_manager.get_variable(left)
            if left_var.volatile:
                return None  # Volatile variable, can't evaluate at compile-time
            left_value = self.var_manager.get_variable_runtime_value(left)
            if left_value is None:
                return None  # Unknown value
            
            # Get right value (constant or variable)
            if CSM.is_decimal(right):
                right_value = CSM.convert_to_decimal(right)
            elif self.var_manager.check_variable_exists(right):
                right_var = self.var_manager.get_variable(right)
                if right_var.volatile:
                    return None
                right_value = self.var_manager.get_variable_runtime_value(right)
                if right_value is None:
                    return None
            else:
                return None
            
            # Evaluate condition
            if condition.type == ConditionTypes.GREATER_THAN:
                return left_value > right_value
            elif condition.type == ConditionTypes.LESS_THAN:
                return left_value < right_value
            elif condition.type == ConditionTypes.EQUAL:
                return left_value == right_value
            elif condition.type == ConditionTypes.NOT_EQUAL:
                return left_value != right_value
            elif condition.type == ConditionTypes.GREATER_EQUAL:
                return left_value >= right_value
            elif condition.type == ConditionTypes.LESS_EQUAL:
                return left_value <= right_value
            else:
                return None
        except Exception as e:
            logger.debug(f"Failed to evaluate condition at compile-time: {e}")
            return None
    
    def __get_modified_variables(self, grouped_lines: list[Command]) -> set[str]:
        """Extract list of variable names that were modified in given command list."""
        modified = set()
        
        # Recursively check all commands including nested if-else and while blocks
        for cmd in grouped_lines:
            # Direct assignment
            if isinstance(cmd, AssignCommand):
                modified.add(cmd.var_name)
                logger.debug(f"Detected modification of variable '{cmd.var_name}'")
            
            # Nested if-else blocks
            elif hasattr(cmd, 'command_type') and cmd.command_type == CommandTypes.IF:
                if isinstance(cmd.line, IfElseClause):
                    clause = cmd.line
                    # Check if branch
                    if clause.get_if() is not None:
                        modified.update(self.__get_modified_variables(clause.get_if().get_lines()))
                    # Check elif branches
                    for elif_clause in clause.get_elif():
                        modified.update(self.__get_modified_variables(elif_clause.get_lines()))
                    # Check else branch
                    if clause.get_else() is not None:
                        modified.update(self.__get_modified_variables(clause.get_else().get_lines()))
            
            # Nested while loops
            elif hasattr(cmd, 'command_type') and cmd.command_type == CommandTypes.WHILE:
                if isinstance(cmd.line, WhileClause):
                    modified.update(self.__get_modified_variables(cmd.line.get_lines()))
        
        return modified
    
    def __invalidate_modified_variables(self, grouped_lines: list[Command]) -> None:
        """Invalidate runtime values for variables modified in given command list."""
        for var_name in self.__get_modified_variables(grouped_lines):
            if self.var_manager.check_variable_exists(var_name):
                self.var_manager.invalidate_runtime_value(var_name)
                logger.debug(f"Invalidated runtime value for '{var_name}' (modified in conditional block)")

    def __set_reg_const(self, reg: Register, value: int) -> int:
        """Build constant into register, reusing existing const registers if possible."""
        value &= 0xFF
        return self.__build_const_in_reg(value, reg)

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
    
    def __peephole_optimize(self, lines: list[str]) -> list[str]:
        """Apply peephole optimizations to assembly code.
        
        Optimizations:
        1. Remove dead LDI: ldi #X followed by ldi #Y → ldi #Y
        2. Remove redundant MOV: mov X, X → (removed)
        3. Remove dead stores before immediate overwrite
        """
        if not lines:
            return lines
        
        optimized = []
        i = 0
        
        while i < len(lines):
            current = lines[i].strip()
            
            # Skip labels and empty lines
            if not current or current.endswith(':'):
                optimized.append(lines[i])
                i += 1
                continue
            
            # Look ahead for optimization opportunities
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                
                # Pattern 1: ldi #X followed by ldi #Y (dead LDI)
                if current.startswith('ldi #') and next_line.startswith('ldi #'):
                    logger.debug(f"Peephole: Removing dead LDI: '{current}' (overwritten by '{next_line}')")
                    i += 1  # Skip current, keep next
                    continue
                
                # Pattern 2: Load to register followed by immediate overwrite
                # Example: mov rd, m followed by ldi #X; mov rd, ra
                if current.startswith('mov rd, m') and i + 2 < len(lines):
                    line2 = lines[i + 1].strip()
                    line3 = lines[i + 2].strip() if i + 2 < len(lines) else ""
                    
                    if line2.startswith('ldi #') and line3 == 'mov rd, ra':
                        # RD loaded from memory but immediately overwritten
                        logger.debug(f"Peephole: Removing dead load sequence: '{current}', '{line2}', '{line3}'")
                        # Skip the load, keep the LDI sequence
                        i += 1
                        continue
            
            optimized.append(lines[i])
            i += 1
        
        return optimized
    
    @staticmethod
    def __determine_command_type(line:str) -> str:
        if re.match(r'^\w+\s*=\s*.+$', line):
            return "assign"
        return None
            

def create_default_compiler() -> Compiler:
    return Compiler(comment_char='//', variable_start_addr=0x0000, 
                    variable_end_addr=0x0200, memory_size=65536)


def main():
    # Setup logging for test execution
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
    
    compiler = create_default_compiler()
    
    compiler.load_lines('files/volatile_test.arn')
    compiler.break_commands()
    compiler.clean_lines()
    compiler.group_commands()
    logger.info(f"Grouped {len(compiler.grouped_lines)} commands")
    compiler.compile_lines()
    new_exp = compiler._change_expression_with_var_values("a + 5 -b + 3")
    compiler._simplify_expression(new_exp)

    logger.info(f"Generated {len(compiler.assembly_lines)} assembly lines")
    for line in compiler.assembly_lines:
        print(line)
if __name__ == "__main__":
    main()
