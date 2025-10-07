import logging
from MyEnums import ConditionTypes, ExpressionTypes, MATH_OPERATORS

logger = logging.getLogger(__name__)

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
        return int(int_str[2:], 16)
    elif int_str.startswith('0b'):
        return int(int_str[2:], 2)
    else:
        try:
            return int(int_str)
        except ValueError:
            return None
        
def get_decimal_byte_count(value:int) -> int:
    """
    Returns the number of bytes required to represent the given integer value.
    """
    if value < 0:
        raise ValueError("Negative values are not supported.")
    elif value <= 0xFF:
        return 1
    elif value <= 0xFFFF:
        return 2
    elif value <= 0xFFFFFFFF:
        return 4
    else:
        raise ValueError("Value too large to be represented in 4 bytes.")

def get_decimal_bytes(value:int) -> list[int]:
    """
    Returns a list of bytes representing the given integer value in little-endian order.
    """
    if value < 0:
        raise ValueError("Negative values are not supported.")
    
    byte_count = get_decimal_byte_count(value)
    return [(value >> (8 * i)) & 0xFF for i in range(byte_count)]

def is_decimal(expression:str):
    return convert_to_decimal(expression) != None

def split_expression(expression:str):
    splitted:list[str] = []
    buffer:list[str] = []
    for c in expression:
        buffer.append(c)
        if c == ' ' or c in MATH_OPERATORS:
            word = ''.join(buffer).strip()
            if word != "":
                splitted.append(word)
            buffer = []
    splitted.append(''.join(buffer).strip())
    return splitted

def check_marl_increment(current_address:int, target_address:int, max_allowed_increment:int) -> bool:
    pass

def inc_steps_to_target(current: int, target: int) -> int:
    max_val = 0xFF
    steps = (target - current) % max_val
    if steps == 0 and current != target:
        steps = max_val
    return steps
     
def get_expression_type(expression:str):
    expression = expression.strip()
    splitted = split_expression(expression)
    logger.debug(f"Expression split result: {splitted}")
    # Is single?
    if len(splitted) == 1:
        if is_decimal(splitted[0]):
            return ExpressionTypes.SINGLE_DEC
        else:
            return ExpressionTypes.SINGLE_VAR
    
    #Is all decimal?
    is_all_dec = True
    for exp in splitted:
        if exp in MATH_OPERATORS:
            continue
        if not is_decimal(exp):
            is_all_dec = False
            break
    if is_all_dec:
        return ExpressionTypes.ALL_DEC
    
    raise ValueError(f"Unsupported Expression Type : {expression}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger.info(f"inc_steps_to_target(255, 1) = {inc_steps_to_target(255, 1)}")
    logger.info(f"inc_steps_to_target(0, 1) = {inc_steps_to_target(0, 1)}")
    logger.info(f"inc_steps_to_target(0, 2) = {inc_steps_to_target(0, 2)}")
    logger.info(f"inc_steps_to_target(254, 1) = {inc_steps_to_target(254, 1)}")
    