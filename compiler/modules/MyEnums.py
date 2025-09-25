from enum import StrEnum

class WhileTypes(StrEnum):
    CONDITIONAL = "conditional"
    INFINITE = "infinite"
    BYPASS = "bypass"

class ConditionTypes(StrEnum):
    EQUAL = "=="
    NOT_EQUAL = "!="
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    GREATER_THAN = ">"
    LESS_THAN = "<"

class ExpressionTypes(StrEnum):
    SINGLE_DEC= "single_decimal"
    SINGLE_VAR="single_var"
    ALL_DEC = "all_dec"

class MathOperators(StrEnum):
    PLUS='+'
    MINUS='-'
    MUL='*'
    DIV='/'
    AND='&'
    OR='|'

MATH_OPERATORS = list(MathOperators._value2member_map_.keys())