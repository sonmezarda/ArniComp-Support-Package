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