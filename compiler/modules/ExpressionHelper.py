"""
Expression simplification for compiler.
Supports: +, -, *, /, &, |, ^, <<, >>, (), operator precedence
"""

import re
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)


class ExpressionTokenizer:
    """Tokenizes expressions with support for multi-char operators."""
    
    SINGLE_CHAR_OPS = {'+', '-', '*', '/', '&', '|', '^', '(', ')'}
    MULTI_CHAR_OPS = {'<<', '>>'}
    
    @staticmethod
    def tokenize(expression: str) -> List[str]:
        """Convert expression to token list."""
        expr = re.sub(r'\s+', '', expression)
        if not expr:
            return []
        
        tokens = []
        i = 0
        
        while i < len(expr):
            # Check for multi-char operators
            if i < len(expr) - 1:
                two_char = expr[i:i+2]
                if two_char in ExpressionTokenizer.MULTI_CHAR_OPS:
                    tokens.append(two_char)
                    i += 2
                    continue
            
            # Single char operator or parenthesis
            if expr[i] in ExpressionTokenizer.SINGLE_CHAR_OPS:
                tokens.append(expr[i])
                i += 1
            else:
                # Build number or variable
                start = i
                while i < len(expr) and expr[i] not in ExpressionTokenizer.SINGLE_CHAR_OPS:
                    # Check if we're about to hit a multi-char operator
                    if i < len(expr) - 1 and expr[i:i+2] in ExpressionTokenizer.MULTI_CHAR_OPS:
                        break
                    i += 1
                tokens.append(expr[start:i])
        
        return tokens
    
    @staticmethod
    def is_number(token: str) -> bool:
        """Check if token is numeric (decimal, hex, binary)."""
        token = token.strip().lower()
        if token.startswith('0x'):
            try:
                int(token, 16)
                return True
            except ValueError:
                return False
        elif token.startswith('0b'):
            try:
                int(token, 2)
                return True
            except ValueError:
                return False
        else:
            try:
                float(token)
                return True
            except (ValueError, AttributeError):
                return False
    
    @staticmethod
    def parse_number(token: str) -> int:
        """Parse number from various formats (decimal, hex, binary)."""
        token = token.strip().lower()
        if token.startswith('0x'):
            return int(token, 16)
        elif token.startswith('0b'):
            return int(token, 2)
        else:
            return int(float(token))


class TermRepresentation:
    """
    Represents expression terms for compiler optimization.
    Handles both algebraic (a+b) and bitwise (a&b) operations.
    For bitwise ops with variables, keeps them symbolic.
    """
    
    CONSTANT_KEY = '__const__'
    
    def __init__(self, terms: Optional[Dict[str, float]] = None, 
                 is_bitwise: bool = False,
                 bitwise_expr: Optional[str] = None):
        self.terms = defaultdict(float)
        if terms:
            self.terms.update(terms)
        self.is_bitwise = is_bitwise
        self.bitwise_expr = bitwise_expr  # Keep symbolic for variable bitwise ops
    
    @classmethod
    def from_constant(cls, value: float) -> 'TermRepresentation':
        return cls({cls.CONSTANT_KEY: value})
    
    @classmethod
    def from_variable(cls, variable: str, coefficient: float = 1.0) -> 'TermRepresentation':
        return cls({variable: coefficient})
    
    @classmethod
    def from_bitwise(cls, expr: str) -> 'TermRepresentation':
        """Create symbolic bitwise expression."""
        return cls(is_bitwise=True, bitwise_expr=expr)
    
    def add(self, other: 'TermRepresentation') -> 'TermRepresentation':
        """Add two terms."""
        # If either is bitwise symbolic, can't simplify algebraically
        if self.is_bitwise or other.is_bitwise:
            combined = f"({self.bitwise_expr or self._to_expr()}) + ({other.bitwise_expr or other._to_expr()})"
            return TermRepresentation.from_bitwise(combined)
        
        result = TermRepresentation(dict(self.terms))
        for var, coef in other.terms.items():
            result.terms[var] += coef
        return result
    
    def negate(self) -> 'TermRepresentation':
        if self.is_bitwise:
            return TermRepresentation.from_bitwise(f"-({self.bitwise_expr})")
        return TermRepresentation({var: -coef for var, coef in self.terms.items()})
    
    def multiply(self, other: 'TermRepresentation') -> 'TermRepresentation':
        """Multiply terms."""
        if self.is_bitwise or other.is_bitwise:
            combined = f"({self.bitwise_expr or self._to_expr()}) * ({other.bitwise_expr or other._to_expr()})"
            return TermRepresentation.from_bitwise(combined)
        
        a_const = self.terms.get(self.CONSTANT_KEY, 0)
        b_const = other.terms.get(self.CONSTANT_KEY, 0)
        a_vars = {k: v for k, v in self.terms.items() if k != self.CONSTANT_KEY}
        b_vars = {k: v for k, v in other.terms.items() if k != self.CONSTANT_KEY}
        
        if not a_vars and not b_vars:
            return TermRepresentation.from_constant(a_const * b_const)
        
        if not a_vars:
            return TermRepresentation({var: coef * a_const for var, coef in other.terms.items()})
        
        if not b_vars:
            return TermRepresentation({var: coef * b_const for var, coef in self.terms.items()})
        
        # Variable products - create combined keys
        result = {}
        for var_a, coef_a in a_vars.items():
            for var_b, coef_b in b_vars.items():
                prod_key = '*'.join(sorted([var_a, var_b]))
                result[prod_key] = result.get(prod_key, 0) + coef_a * coef_b
        
        if a_const != 0:
            for var, coef in other.terms.items():
                result[var] = result.get(var, 0) + a_const * coef
        
        if b_const != 0:
            for var, coef in a_vars.items():
                result[var] = result.get(var, 0) + b_const * coef
        
        if a_const != 0 and b_const != 0:
            result[self.CONSTANT_KEY] = result.get(self.CONSTANT_KEY, 0) + a_const * b_const
        
        return TermRepresentation(result)
    
    def divide(self, other: 'TermRepresentation') -> 'TermRepresentation':
        """Divide by constant only."""
        if self.is_bitwise or other.is_bitwise:
            combined = f"({self.bitwise_expr or self._to_expr()}) / ({other.bitwise_expr or other._to_expr()})"
            return TermRepresentation.from_bitwise(combined)
        
        b_const = other.terms.get(self.CONSTANT_KEY, 0)
        b_vars = {k: v for k, v in other.terms.items() if k != self.CONSTANT_KEY}
        
        if b_vars:
            raise NotImplementedError("Division by variable not supported")
        
        if abs(b_const) < 1e-9:
            raise ValueError("Division by zero")
        
        return TermRepresentation({var: coef / b_const for var, coef in self.terms.items()})
    
    def bitwise_and(self, other: 'TermRepresentation') -> 'TermRepresentation':
        """Bitwise AND operation."""
        # Both constants? Compute directly
        if self.is_pure_constant() and other.is_pure_constant():
            val = int(self.terms[self.CONSTANT_KEY]) & int(other.terms[self.CONSTANT_KEY])
            return TermRepresentation.from_constant(val)
        
        # Otherwise keep symbolic
        left = self.bitwise_expr or self._to_expr()
        right = other.bitwise_expr or other._to_expr()
        return TermRepresentation.from_bitwise(f"({left}) & ({right})")
    
    def bitwise_or(self, other: 'TermRepresentation') -> 'TermRepresentation':
        """Bitwise OR operation."""
        if self.is_pure_constant() and other.is_pure_constant():
            val = int(self.terms[self.CONSTANT_KEY]) | int(other.terms[self.CONSTANT_KEY])
            return TermRepresentation.from_constant(val)
        
        left = self.bitwise_expr or self._to_expr()
        right = other.bitwise_expr or other._to_expr()
        return TermRepresentation.from_bitwise(f"({left}) | ({right})")
    
    def bitwise_xor(self, other: 'TermRepresentation') -> 'TermRepresentation':
        """Bitwise XOR operation."""
        if self.is_pure_constant() and other.is_pure_constant():
            val = int(self.terms[self.CONSTANT_KEY]) ^ int(other.terms[self.CONSTANT_KEY])
            return TermRepresentation.from_constant(val)
        
        left = self.bitwise_expr or self._to_expr()
        right = other.bitwise_expr or other._to_expr()
        return TermRepresentation.from_bitwise(f"({left}) ^ ({right})")
    
    def shift_left(self, other: 'TermRepresentation') -> 'TermRepresentation':
        """Left shift operation."""
        if self.is_pure_constant() and other.is_pure_constant():
            val = int(self.terms[self.CONSTANT_KEY]) << int(other.terms[self.CONSTANT_KEY])
            return TermRepresentation.from_constant(val)
        
        left = self.bitwise_expr or self._to_expr()
        right = other.bitwise_expr or other._to_expr()
        return TermRepresentation.from_bitwise(f"({left}) << ({right})")
    
    def shift_right(self, other: 'TermRepresentation') -> 'TermRepresentation':
        """Right shift operation."""
        if self.is_pure_constant() and other.is_pure_constant():
            val = int(self.terms[self.CONSTANT_KEY]) >> int(other.terms[self.CONSTANT_KEY])
            return TermRepresentation.from_constant(val)
        
        left = self.bitwise_expr or self._to_expr()
        right = other.bitwise_expr or other._to_expr()
        return TermRepresentation.from_bitwise(f"({left}) >> ({right})")
    
    def clean(self, epsilon: float = 1e-9) -> 'TermRepresentation':
        """Remove near-zero terms."""
        if self.is_bitwise:
            return self
        cleaned = {var: coef for var, coef in self.terms.items() if abs(coef) > epsilon}
        return TermRepresentation(cleaned)
    
    def to_dict(self) -> Dict[str, float]:
        return dict(self.terms)
    
    def is_empty(self) -> bool:
        return not self.is_bitwise and all(abs(coef) < 1e-9 for coef in self.terms.values())
    
    def is_pure_constant(self) -> bool:
        return not self.is_bitwise and len(self.terms) == 1 and self.CONSTANT_KEY in self.terms
    
    def get_constant_value(self) -> Optional[float]:
        if self.is_pure_constant():
            return self.terms[self.CONSTANT_KEY]
        return None
    
    def _to_expr(self) -> str:
        """Convert algebraic terms to expression string."""
        if len(self.terms) == 1 and self.CONSTANT_KEY in self.terms:
            val = self.terms[self.CONSTANT_KEY]
            return str(int(val) if val == int(val) else val)
        
        parts = []
        for var in sorted(self.terms.keys()):
            if var == self.CONSTANT_KEY:
                continue
            coef = self.terms[var]
            if abs(coef - 1) < 1e-9:
                parts.append(var)
            else:
                parts.append(f"{int(coef) if coef == int(coef) else coef}*{var}")
        
        const = self.terms.get(self.CONSTANT_KEY, 0)
        if abs(const) > 1e-9:
            parts.append(str(int(const) if const == int(const) else const))
        
        return '+'.join(parts) if parts else "0"


class ExpressionParser:
    """
    Recursive descent parser with operator precedence.
    Grammar (lowest to highest precedence):
        bitwise_or    := bitwise_xor ('|' bitwise_xor)*
        bitwise_xor   := bitwise_and ('^' bitwise_and)*
        bitwise_and   := shift ('&' shift)*
        shift         := expression (('<<' | '>>') expression)*
        expression    := term (('+' | '-') term)*
        term          := factor (('*' | '/') factor)*
        factor        := number | variable | '(' bitwise_or ')' | unary
    """
    
    def __init__(self, tokens: List[str]):
        self.tokens = tokens
        self.pos = 0
    
    def parse(self) -> TermRepresentation:
        if not self.tokens:
            return TermRepresentation.from_constant(0)
        
        result = self._parse_bitwise_or()
        
        if self.pos < len(self.tokens):
            logger.warning(f"Unexpected tokens: {self.tokens[self.pos:]}")
        
        return result
    
    def _peek(self) -> Optional[str]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None
    
    def _consume(self) -> str:
        token = self.tokens[self.pos]
        self.pos += 1
        return token
    
    def _parse_bitwise_or(self) -> TermRepresentation:
        """Bitwise OR (lowest precedence)."""
        left = self._parse_bitwise_xor()
        
        while self._peek() == '|':
            self._consume()
            right = self._parse_bitwise_xor()
            left = left.bitwise_or(right)
        
        return left
    
    def _parse_bitwise_xor(self) -> TermRepresentation:
        """Bitwise XOR."""
        left = self._parse_bitwise_and()
        
        while self._peek() == '^':
            self._consume()
            right = self._parse_bitwise_and()
            left = left.bitwise_xor(right)
        
        return left
    
    def _parse_bitwise_and(self) -> TermRepresentation:
        """Bitwise AND."""
        left = self._parse_shift()
        
        while self._peek() == '&':
            self._consume()
            right = self._parse_shift()
            left = left.bitwise_and(right)
        
        return left
    
    def _parse_shift(self) -> TermRepresentation:
        """Shift operators."""
        left = self._parse_expression()
        
        while self._peek() in ['<<', '>>']:
            op = self._consume()
            right = self._parse_expression()
            if op == '<<':
                left = left.shift_left(right)
            else:
                left = left.shift_right(right)
        
        return left
    
    def _parse_expression(self) -> TermRepresentation:
        """Addition and subtraction."""
        left = self._parse_term()
        
        while self._peek() in ['+', '-']:
            op = self._consume()
            right = self._parse_term()
            
            if op == '+':
                left = left.add(right)
            else:
                left = left.add(right.negate())
        
        return left
    
    def _parse_term(self) -> TermRepresentation:
        """Multiplication and division."""
        left = self._parse_factor()
        
        while self._peek() in ['*', '/']:
            op = self._consume()
            right = self._parse_factor()
            
            if op == '*':
                left = left.multiply(right)
            else:
                left = left.divide(right)
        
        return left
    
    def _parse_factor(self) -> TermRepresentation:
        """Atoms and unary operators."""
        token = self._peek()
        
        if token is None:
            raise ValueError("Unexpected end of expression")
        
        # Parenthesized expression
        if token == '(':
            self._consume()
            result = self._parse_bitwise_or()
            if self._peek() == ')':
                self._consume()
            else:
                raise ValueError("Missing ')'")
            return result
        
        # Unary minus
        if token == '-':
            self._consume()
            return self._parse_factor().negate()
        
        # Unary plus
        if token == '+':
            self._consume()
            return self._parse_factor()
        
        # Number or variable
        token = self._consume()
        
        if ExpressionTokenizer.is_number(token):
            val = ExpressionTokenizer.parse_number(token)
            return TermRepresentation.from_constant(val)
        else:
            return TermRepresentation.from_variable(token, 1.0)


class ExpressionFormatter:
    """Format TermRepresentation back to string."""
    
    @staticmethod
    def format(term_repr: TermRepresentation) -> str:
        """Convert TermRepresentation to readable string."""
        # If it's a bitwise symbolic expression, return as-is (cleaned up)
        if term_repr.is_bitwise:
            result = term_repr.bitwise_expr
            # Clean up excessive parentheses if possible
            result = re.sub(r'\(\(([^()]+)\)\)', r'(\1)', result)
            return result
        
        terms = term_repr.clean().to_dict()
        
        if not terms:
            return "0"
        
        const_val = terms.pop(TermRepresentation.CONSTANT_KEY, 0)
        
        # Only constant
        if not terms and const_val != 0:
            return ExpressionFormatter._format_number(const_val)
        
        # Build parts
        parts = []
        for var in sorted(terms.keys()):
            coef = terms[var]
            part = ExpressionFormatter._format_term(var, coef, is_first=(len(parts) == 0))
            if part:
                parts.append(part)
        
        # Add constant
        if abs(const_val) > 1e-9:
            const_str = ExpressionFormatter._format_number(const_val)
            if const_val > 0:
                parts.append(f"+ {const_str}" if parts else const_str)
            else:
                parts.append(f"- {ExpressionFormatter._format_number(abs(const_val))}")
        
        if not parts:
            return "0"
        
        result = ' '.join(parts)
        result = re.sub(r'^\+\s*', '', result)
        
        return result
    
    @staticmethod
    def _format_number(value: float) -> str:
        if value == int(value):
            return str(int(value))
        return str(value)
    
    @staticmethod
    def _format_term(variable: str, coefficient: float, is_first: bool) -> str:
        if abs(coefficient) < 1e-9:
            return ""
        
        abs_coef = abs(coefficient)
        is_negative = coefficient < 0
        
        # Coefficient formatting
        if abs(abs_coef - 1.0) < 1e-9:
            coef_str = ""
        else:
            coef_str = ExpressionFormatter._format_number(abs_coef) + " * "
        
        term = f"{coef_str}{variable}"
        
        if is_first:
            return f"- {term}" if is_negative else term
        else:
            return f"- {term}" if is_negative else f"+ {term}"


class ExpressionSimplifier:
    """Expression simplifier for compiler optimization."""
    
    @staticmethod
    def simplify(expression: str) -> str:
        """
        Simplify expression to reduced form.
        Supports: +, -, *, /, &, |, ^, <<, >>, ()
        
        Examples:
            "a + b - a" -> "b"
            "a + 10 - 5 + c - 20" -> "a + c - 15"
            "2 * 3 + 4" -> "10"
            "0xFF & 0x0F" -> "15"
        """
        if not expression or not expression.strip():
            return "0"
        
        try:
            tokens = ExpressionTokenizer.tokenize(expression)
            if not tokens:
                return "0"
            
            parser = ExpressionParser(tokens)
            term_repr = parser.parse()
            
            term_repr = term_repr.clean()
            
            if term_repr.is_empty():
                return "0"
            
            result = ExpressionFormatter.format(term_repr)
            logger.debug(f"Simplified '{expression}' -> '{result}'")
            
            return result
            
        except Exception as e:
            logger.warning(f"Failed to simplify '{expression}': {e}")
            return expression


def simplify_expression(expression: str) -> str:
    """Convenience function for expression simplification."""
    return ExpressionSimplifier.simplify(expression)


# ============================================================================
# COMPILATION PLANNING
# ============================================================================
# Note: Assembly generation is handled by CompilerHelper, not here.
# This module only provides:
#   1. Expression simplification (simplify_expression)
#   2. Compilation step planning (plan_compilation)
# CompilerHelper uses these functions and generates assembly based on its own
# register management, MAR optimization, and runtime value tracking.
# ============================================================================

class CompilationStep:
    """Represents a single operation step for compiler code generation."""
    
    def __init__(self, operation: str, left: str, right: str, result_temp: str):
        self.operation = operation  # '+', '-', '*', '/', '&', '|', '^', '<<', '>>'
        self.left = left  # Variable name, temp var, or constant
        self.right = right  # Variable name, temp var, or constant
        self.result_temp = result_temp  # Temp variable holding result
    
    def __repr__(self):
        return f"Step({self.result_temp} = {self.left} {self.operation} {self.right})"
    
    def __str__(self):
        return f"{self.result_temp} = {self.left} {self.operation} {self.right}"


class ExpressionCompilationPlanner:
    """
    Plans compilation steps for expressions with proper operator precedence.
    Generates a sequence of operations that compiler can execute in order.
    """
    
    def __init__(self):
        self.temp_counter = 0
        self.steps: List[CompilationStep] = []
    
    def _new_temp(self) -> str:
        """Generate a new temporary variable name."""
        temp = f"_t{self.temp_counter}"
        self.temp_counter += 1
        return temp
    
    def plan(self, expression: str) -> Tuple[List[CompilationStep], str]:
        """
        Plan compilation steps for expression.
        
        Args:
            expression: Expression string to plan
            
        Returns:
            Tuple of (steps_list, final_result_temp)
            - steps_list: Ordered list of CompilationStep objects
            - final_result_temp: Name of temp var holding final result
        
        Example:
            >>> planner = ExpressionCompilationPlanner()
            >>> steps, result = planner.plan("a * b + 10")
            >>> for step in steps:
            ...     print(step)
            _t0 = a * b
            _t1 = _t0 + 10
            >>> print(result)
            _t1
        """
        self.steps = []
        self.temp_counter = 0
        
        tokens = ExpressionTokenizer.tokenize(expression)
        if not tokens:
            return [], "0"
        
        parser = ExpressionCompilationParser(tokens, self)
        final_result = parser.parse()
        
        return self.steps, final_result
    
    def _add_step(self, op: str, left: str, right: str) -> str:
        """Add a compilation step and return the temp var holding result."""
        result_temp = self._new_temp()
        step = CompilationStep(op, left, right, result_temp)
        self.steps.append(step)
        return result_temp


class ExpressionCompilationParser:
    """
    Parser that generates compilation steps instead of simplifying.
    Maintains same precedence as ExpressionParser but outputs step sequence.
    """
    
    def __init__(self, tokens: List[str], planner: ExpressionCompilationPlanner):
        self.tokens = tokens
        self.pos = 0
        self.planner = planner
    
    def parse(self) -> str:
        """Parse and return final result temp var."""
        if not self.tokens:
            return "0"
        
        result = self._parse_bitwise_or()
        
        if self.pos < len(self.tokens):
            logger.warning(f"Unexpected tokens: {self.tokens[self.pos:]}")
        
        return result
    
    def _peek(self) -> Optional[str]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None
    
    def _consume(self) -> str:
        token = self.tokens[self.pos]
        self.pos += 1
        return token
    
    def _parse_bitwise_or(self) -> str:
        """Bitwise OR (lowest precedence)."""
        left = self._parse_bitwise_xor()
        
        while self._peek() == '|':
            self._consume()
            right = self._parse_bitwise_xor()
            left = self.planner._add_step('|', left, right)
        
        return left
    
    def _parse_bitwise_xor(self) -> str:
        """Bitwise XOR."""
        left = self._parse_bitwise_and()
        
        while self._peek() == '^':
            self._consume()
            right = self._parse_bitwise_and()
            left = self.planner._add_step('^', left, right)
        
        return left
    
    def _parse_bitwise_and(self) -> str:
        """Bitwise AND."""
        left = self._parse_shift()
        
        while self._peek() == '&':
            self._consume()
            right = self._parse_shift()
            left = self.planner._add_step('&', left, right)
        
        return left
    
    def _parse_shift(self) -> str:
        """Shift operators."""
        left = self._parse_expression()
        
        while self._peek() in ['<<', '>>']:
            op = self._consume()
            right = self._parse_expression()
            left = self.planner._add_step(op, left, right)
        
        return left
    
    def _parse_expression(self) -> str:
        """Addition and subtraction."""
        left = self._parse_term()
        
        while self._peek() in ['+', '-']:
            op = self._consume()
            right = self._parse_term()
            left = self.planner._add_step(op, left, right)
        
        return left
    
    def _parse_term(self) -> str:
        """Multiplication and division."""
        left = self._parse_factor()
        
        while self._peek() in ['*', '/']:
            op = self._consume()
            right = self._parse_factor()
            left = self.planner._add_step(op, left, right)
        
        return left
    
    def _parse_factor(self) -> str:
        """Atoms and unary operators."""
        token = self._peek()
        
        if token is None:
            raise ValueError("Unexpected end of expression")
        
        # Parenthesized expression
        if token == '(':
            self._consume()
            result = self._parse_bitwise_or()
            if self._peek() == ')':
                self._consume()
            else:
                raise ValueError("Missing ')'")
            return result
        
        # Unary minus - create a step: temp = 0 - value
        if token == '-':
            self._consume()
            operand = self._parse_factor()
            return self.planner._add_step('-', '0', operand)
        
        # Unary plus - just return the value
        if token == '+':
            self._consume()
            return self._parse_factor()
        
        # Number or variable - return as-is (no step needed)
        token = self._consume()
        return token


class ISAOptimizer:
    """Represents a single operation step for compiler code generation."""
    
    def __init__(self, operation: str, left: str, right: str, result_temp: str):
        self.operation = operation  # '+', '-', '*', '/', '&', '|', '^', '<<', '>>'
        self.left = left  # Variable name, temp var, or constant
        self.right = right  # Variable name, temp var, or constant
        self.result_temp = result_temp  # Temp variable holding result
    
    def __repr__(self):
        return f"Step({self.result_temp} = {self.left} {self.operation} {self.right})"
    
    def __str__(self):
        return f"{self.result_temp} = {self.left} {self.operation} {self.right}"


class ExpressionCompilationPlanner:
    """
    Plans compilation steps for expressions with proper operator precedence.
    Generates a sequence of operations that compiler can execute in order.
    """
    
    def __init__(self):
        self.temp_counter = 0
        self.steps: List[CompilationStep] = []
    
    def _new_temp(self) -> str:
        """Generate a new temporary variable name."""
        temp = f"_t{self.temp_counter}"
        self.temp_counter += 1
        return temp
    
    def plan(self, expression: str) -> Tuple[List[CompilationStep], str]:
        """
        Plan compilation steps for expression.
        
        Args:
            expression: Expression string to plan
            
        Returns:
            Tuple of (steps_list, final_result_temp)
            - steps_list: Ordered list of CompilationStep objects
            - final_result_temp: Name of temp var holding final result
        
        Example:
            >>> planner = ExpressionCompilationPlanner()
            >>> steps, result = planner.plan("a * b + 10")
            >>> for step in steps:
            ...     print(step)
            _t0 = a * b
            _t1 = _t0 + 10
            >>> print(result)
            _t1
        """
        self.steps = []
        self.temp_counter = 0
        
        tokens = ExpressionTokenizer.tokenize(expression)
        if not tokens:
            return [], "0"
        
        parser = ExpressionCompilationParser(tokens, self)
        final_result = parser.parse()
        
        return self.steps, final_result
    
    def _add_step(self, op: str, left: str, right: str) -> str:
        """Add a compilation step and return the temp var holding result."""
        result_temp = self._new_temp()
        step = CompilationStep(op, left, right, result_temp)
        self.steps.append(step)
        return result_temp


class ExpressionCompilationParser:
    """
    Parser that generates compilation steps instead of simplifying.
    Maintains same precedence as ExpressionParser but outputs step sequence.
    """
    
    def __init__(self, tokens: List[str], planner: ExpressionCompilationPlanner):
        self.tokens = tokens
        self.pos = 0
        self.planner = planner
    
    def parse(self) -> str:
        """Parse and return final result temp var."""
        if not self.tokens:
            return "0"
        
        result = self._parse_bitwise_or()
        
        if self.pos < len(self.tokens):
            logger.warning(f"Unexpected tokens: {self.tokens[self.pos:]}")
        
        return result
    
    def _peek(self) -> Optional[str]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None
    
    def _consume(self) -> str:
        token = self.tokens[self.pos]
        self.pos += 1
        return token
    
    def _parse_bitwise_or(self) -> str:
        """Bitwise OR (lowest precedence)."""
        left = self._parse_bitwise_xor()
        
        while self._peek() == '|':
            self._consume()
            right = self._parse_bitwise_xor()
            left = self.planner._add_step('|', left, right)
        
        return left
    
    def _parse_bitwise_xor(self) -> str:
        """Bitwise XOR."""
        left = self._parse_bitwise_and()
        
        while self._peek() == '^':
            self._consume()
            right = self._parse_bitwise_and()
            left = self.planner._add_step('^', left, right)
        
        return left
    
    def _parse_bitwise_and(self) -> str:
        """Bitwise AND."""
        left = self._parse_shift()
        
        while self._peek() == '&':
            self._consume()
            right = self._parse_shift()
            left = self.planner._add_step('&', left, right)
        
        return left
    
    def _parse_shift(self) -> str:
        """Shift operators."""
        left = self._parse_expression()
        
        while self._peek() in ['<<', '>>']:
            op = self._consume()
            right = self._parse_expression()
            left = self.planner._add_step(op, left, right)
        
        return left
    
    def _parse_expression(self) -> str:
        """Addition and subtraction."""
        left = self._parse_term()
        
        while self._peek() in ['+', '-']:
            op = self._consume()
            right = self._parse_term()
            left = self.planner._add_step(op, left, right)
        
        return left
    
    def _parse_term(self) -> str:
        """Multiplication and division."""
        left = self._parse_factor()
        
        while self._peek() in ['*', '/']:
            op = self._consume()
            right = self._parse_factor()
            left = self.planner._add_step(op, left, right)
        
        return left
    
    def _parse_factor(self) -> str:
        """Atoms and unary operators."""
        token = self._peek()
        
        if token is None:
            raise ValueError("Unexpected end of expression")
        
        # Parenthesized expression
        if token == '(':
            self._consume()
            result = self._parse_bitwise_or()
            if self._peek() == ')':
                self._consume()
            else:
                raise ValueError("Missing ')'")
            return result
        
        # Unary minus - create a step: temp = 0 - value
        if token == '-':
            self._consume()
            operand = self._parse_factor()
            return self.planner._add_step('-', '0', operand)
        
        # Unary plus - just return the value
        if token == '+':
            self._consume()
            return self._parse_factor()
        
        # Number or variable - return as-is (no step needed)
        token = self._consume()
        return token


class ISAOptimizer:
    """
    ISA-aware optimizer for ArniComp (only ADD, ADC, SUB, SBC, AND, XOR, NOT available).
    Expands operations not supported by ISA into equivalent supported operations.
    """
    
    @staticmethod
    def expand_multiply_by_constant(operand: str, constant: int) -> List[Tuple[str, str, str]]:
        """
        Expand multiplication by constant to repeated additions.
        
        Args:
            operand: Variable/temp to multiply
            constant: Integer constant multiplier
            
        Returns:
            List of (operation, left, right) tuples for repeated addition
            
        Example:
            expand_multiply_by_constant("a", 3) returns:
            [("ADD", "a", "a"), ("ADD", "_prev", "a")]
        """
        if constant == 0:
            return [("ZERO", "", "")]
        
        if constant == 1:
            return []  # No operation needed
        
        operations = []
        abs_const = abs(constant)
        
        # First addition: operand + operand
        operations.append(("+", operand, operand))
        
        # Subsequent additions
        for i in range(abs_const - 2):
            operations.append(("+", "_prev", operand))
        
        # If negative, negate result
        if constant < 0:
            operations.append(("-", "0", "_prev"))
        
        return operations
    
    @staticmethod
    def expand_shift_left(operand: str, amount: int) -> List[Tuple[str, str, str]]:
        """
        Expand left shift to multiplication by power of 2, then to repeated addition.
        a << 2 = a * 4 = a + a + a + a
        """
        multiplier = 2 ** amount
        return ISAOptimizer.expand_multiply_by_constant(operand, multiplier)
    
    @staticmethod
    def estimate_cost(op: str) -> int:
        """
        Estimate instruction cost for operation.
        
        ISA operations (cheap):
        - ADD, SUB, AND, XOR, NOT: ~3-5 instructions each
        
        Software operations (expensive):
        - MUL: ~15-30 instructions
        - DIV: ~30-50 instructions
        - SHIFT: ~5-10 instructions per bit
        """
        if op in ['+', '-', '&', '^']:
            return 3
        elif op == '*':
            return 20  # Software multiplication
        elif op == '/':
            return 40  # Software division
        elif op in ['<<', '>>']:
            return 8  # Shift operations
        elif op == '|':
            return 3  # Bitwise or
        else:
            return 5


class ISAExpressionCompilationPlanner(ExpressionCompilationPlanner):
    """
    Extended planner that expands unsupported operations for ArniComp ISA.
    Handles multiplication by constants with repeated addition.
    """
    
    def __init__(self, optimize: bool = True):
        super().__init__()
        self.optimize = optimize
    
    def _add_step(self, op: str, left: str, right: str) -> str:
        """
        Add compilation step with ISA optimization.
        Expands MUL by constant to repeated ADD.
        """
        # Check if this is multiplication by constant
        if op == '*' and self.optimize:
            left_is_const = ExpressionTokenizer.is_number(left)
            right_is_const = ExpressionTokenizer.is_number(right)
            
            # Multiplication by constant: expand to repeated addition
            if left_is_const and not right_is_const:
                const_val = ExpressionTokenizer.parse_number(left)
                return self._expand_constant_multiply(right, const_val)
            elif right_is_const and not left_is_const:
                const_val = ExpressionTokenizer.parse_number(right)
                return self._expand_constant_multiply(left, const_val)
        
        # Check for shift operations
        if op in ['<<', '>>'] and self.optimize:
            if ExpressionTokenizer.is_number(right):
                shift_amount = ExpressionTokenizer.parse_number(right)
                if op == '<<' and 1 <= shift_amount <= 4:
                    multiplier = 2 ** shift_amount
                    return self._expand_constant_multiply(left, multiplier)
        
        # Default: add as regular step
        return super()._add_step(op, left, right)
    
    def _expand_constant_multiply(self, operand: str, constant: int) -> str:
        """
        Expand constant multiplication to repeated additions.
        
        Key optimization: For (expr)*2, compute expr once, then add to itself.
        This is especially efficient for complex subexpressions.
        
        Examples:
            a * 2 -> a + a (simple operand)
            (a+b) * 2 -> result of (a+b), then add to itself (efficient!)
            a * 3 -> (a + a) + a
            a * 4 -> (a+a) + (a+a) (balanced tree)
        """
        if constant == 0:
            return "0"
        
        if constant == 1:
            return operand
        
        if constant < 0:
            # Handle negative: -(operand * |constant|)
            abs_result = self._expand_constant_multiply(operand, abs(constant))
            return super()._add_step('-', '0', abs_result)
        
        # Special case for multiplying by 2: operand + operand
        # This is efficient even if operand is a complex expression
        if constant == 2:
            return super()._add_step('+', operand, operand)
        
        # For 3: (operand + operand) + operand
        if constant == 3:
            double = super()._add_step('+', operand, operand)
            return super()._add_step('+', double, operand)
        
        # For 4: (operand + operand) + (operand + operand)
        # This is more efficient than ((operand+operand)+operand)+operand
        if constant == 4:
            double = super()._add_step('+', operand, operand)
            return super()._add_step('+', double, double)
        
        # For larger constants (5-8): build efficiently
        # 5 = 4 + 1, 6 = 4 + 2, 7 = 4 + 3, 8 = 4 + 4
        if constant <= 8:
            if constant == 5:
                quad = self._expand_constant_multiply(operand, 4)
                return super()._add_step('+', quad, operand)
            elif constant == 6:
                quad = self._expand_constant_multiply(operand, 4)
                double = self._expand_constant_multiply(operand, 2)
                return super()._add_step('+', quad, double)
            elif constant == 7:
                quad = self._expand_constant_multiply(operand, 4)
                triple = self._expand_constant_multiply(operand, 3)
                return super()._add_step('+', quad, triple)
            elif constant == 8:
                quad = self._expand_constant_multiply(operand, 4)
                return super()._add_step('+', quad, quad)
        
        # For constants > 8, fall back to simple repeated addition
        result = super()._add_step('+', operand, operand)
        for i in range(constant - 2):
            result = super()._add_step('+', result, operand)
        
        return result


def plan_compilation(expression: str, optimize_for_isa: bool = True) -> Tuple[List[CompilationStep], str]:
    """
    Plan compilation steps for an expression with ISA-aware optimization.
    
    Args:
        expression: Expression string to compile
        optimize_for_isa: If True, expand MUL/DIV/SHIFT to ISA operations (ADD/SUB/etc)
        
    Returns:
        Tuple of (steps, final_result)
        - steps: List of CompilationStep objects in execution order
        - final_result: Name of variable/temp holding final result
    
    ISA Optimizations Applied:
        - a * 2 -> a + a
        - a * 3 -> (a + a) + a
        - (a+b) * 2 -> simplified first, then expanded
        - a << 2 -> a * 4 -> repeated addition
    
    Example:
        >>> steps, result = plan_compilation("a * 2 + b")
        >>> for step in steps:
        ...     print(step)
        _t0 = a + a        # Expanded from a * 2
        _t1 = _t0 + b
    """
    # First, simplify the expression algebraically
    # This handles things like (a+b)*2 -> 2a + 2b
    simplified = simplify_expression(expression)
    
    # Use ISA-aware planner if optimization is enabled
    if optimize_for_isa:
        planner = ISAExpressionCompilationPlanner(optimize=True)
    else:
        planner = ExpressionCompilationPlanner()
    
    tokens = ExpressionTokenizer.tokenize(simplified)
    if not tokens:
        return [], "0"
    
    parser = ExpressionCompilationParser(tokens, planner)
    final_result = parser.parse()
    
    return planner.steps, final_result


if __name__ == '__main__':
    print("=" * 70)
    print("PART 1: Expression Simplification Tests")
    print("=" * 70)
    
    # Test cases for compiler
    test_cases = [
        # Algebraic simplification
        ("a + b - a", "b"),
        ("a + 10 - 5 + c - 20", "a + c - 15"),
        ("2 * 3 + 4", "10"),
        ("a * 2 + a * 3", "5 * a"),
        ("(a + b) * 2", "2 * a + 2 * b"),
        ("x - x + y", "y"),
        
        # Bitwise operations
        ("0xFF & 0x0F", "15"),
        ("0b1100 | 0b0011", "15"),
        ("0b1100 ^ 0b0011", "15"),
        ("4 << 2", "16"),
        ("16 >> 2", "4"),
        
        # Mixed (variables in bitwise = symbolic)
        ("a & 0xFF", "(a) & (255)"),
        
        # Division
        ("10 / 2 + 3", "8"),
        
        # Edge cases
        ("a * 0 + b", "b"),
        ("-a + b", "- a + b"),
    ]
    
    passed = 0
    failed = 0
    
    for expr, expected in test_cases:
        result = simplify_expression(expr)
        status = "[OK]" if result == expected else "[X]"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} {expr:30} -> {result:20} (expected: {expected})")
    
    print("=" * 70)
    print(f"Passed: {passed}/{len(test_cases)}, Failed: {failed}/{len(test_cases)}")
    
    print("\n")
    print("=" * 70)
    print("PART 2: Compilation Planning Tests")
    print("=" * 70)
    
    # Compilation planning test cases
    compilation_tests = [
        "a * b + 10",
        "a + b * c",
        "(a + b) * c",
        "a & 0xFF + 10",
        "x * 2 + y * 3 - 5",
        "a << 2 | b",
        "-a + b",
        "a * (b + c)",
    ]
    
    for expr in compilation_tests:
        print(f"\nExpression: {expr}")
        print("-" * 70)
        try:
            steps, result = plan_compilation(expr)
            if steps:
                for i, step in enumerate(steps, 1):
                    print(f"  Step {i}: {step}")
                print(f"  Final result in: {result}")
            else:
                print(f"  Direct value: {result}")
        except Exception as e:
            print(f"  Error: {e}")
    
    print("\n" + "=" * 70)
    
    print("\n")
    print("=" * 70)
    print("PART 3: ISA Optimization Tests (MUL/SHIFT -> ADD expansion)")
    print("=" * 70)
    
    isa_test_cases = [
        "(a+b)*2",      # Simplifies to 2a+2b, then each 2a->a+a
        "a*2",          # Should expand to a + a
        "a*3",          # Should expand to a + a + a
        "a*4",          # Should expand to ((a+a)+a)+a
        "x*2 + y*3",    # Both should expand
        "(a+b)*2 + c",  # Complex case
        "a << 2",       # Shift left by 2 = multiply by 4
    ]
    
    for expr in isa_test_cases:
        print(f"\n{'='*70}")
        print(f"Expression: {expr}")
        print(f"Simplified: {simplify_expression(expr)}")
        print("-" * 70)
        
        # Show compilation plan WITH ISA optimization
        steps_opt, result_opt = plan_compilation(expr, optimize_for_isa=True)
        print("ISA-Optimized steps (MUL expanded to ADD):")
        if steps_opt:
            for i, step in enumerate(steps_opt, 1):
                print(f"  {i}. {step}")
            print(f"  Final: {result_opt}")
        else:
            print(f"  Direct value: {result_opt}")
        
        # Compare with non-optimized for reference
        steps_raw, result_raw = plan_compilation(expr, optimize_for_isa=False)
        print("\nNon-optimized steps (with MUL/SHIFT):")
        if steps_raw:
            for i, step in enumerate(steps_raw, 1):
                print(f"  {i}. {step}")
            print(f"  Final: {result_raw}")
        
        print(f"Cost reduction: {len(steps_raw)} steps -> {len(steps_opt)} steps")
    
    print("\n" + "=" * 70)
    print("\n==> ExpressionHelper provides:")
    print("  1. simplify_expression(expr) - Algebraic simplification")
    print("  2. plan_compilation(expr, optimize_for_isa=True) - Step planning with ISA optimization")
    print("\n==> Assembly generation is handled by CompilerHelper")
    print("  - Uses RegisterManager for register allocation")
    print("  - Uses runtime value tracking for optimization")
    print("  - Uses MAR optimization for memory access")
    print("\n" + "=" * 70)

