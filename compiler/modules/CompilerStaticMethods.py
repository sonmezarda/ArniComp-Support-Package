from ConditionHelper import ConditionTypes

def get_inverted_jump_str(condition:ConditionTypes) -> str:
    """
    Returns the inverted jump string for a given condition type.
    """
    if condition == ConditionTypes.EQUAL:
        return "jne"
    elif condition == ConditionTypes.NOT_EQUAL:
        return "jeq"
    elif condition == ConditionTypes.GREATER_THAN:
        return "jle"
    elif condition == ConditionTypes.LESS_THAN:
        return "jge"
    elif condition == ConditionTypes.GREATER_EQUAL:
        return "jlt"
    elif condition == ConditionTypes.LESS_EQUAL:
        return "jgt"
    else:
        raise ValueError(f"Unsupported condition type: {condition}")

def convert_to_decimal(int_str:str) -> int | None:
    """
    Converts a string representing an integer in various formats (decimal, hex, binary)
    to its decimal integer value.
    """
    int_str = int_str.strip().lower()
    if int_str.startswith('0x'):
        return int(int_str, 16)
    elif int_str.startswith('0b'):
        return int(int_str, 2)
    else:
        try:
            return int(int_str)
        except ValueError:
            return None