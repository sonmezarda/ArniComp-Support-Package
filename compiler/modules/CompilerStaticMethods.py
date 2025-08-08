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
