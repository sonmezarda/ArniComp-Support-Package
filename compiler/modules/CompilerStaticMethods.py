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

def convert_expression_to_postfix(expression:str) -> str:
    """
    Converts an infix expression to postfix notation using the Shunting Yard algorithm.
    """
    precedence = {
        '+': 1,
        '-': 1,
        '*': 2,
        '/': 2,
        '(': 0
    }
    output = []
    operators = []

    for token in expression.split():
        if token.isalnum():  # If the token is an operand
            output.append(token)
        elif token == '(':
            operators.append(token)
        elif token == ')':
            while operators and operators[-1] != '(':
                output.append(operators.pop())
            operators.pop()  # Pop the '('
        else:  # The token is an operator
            while (operators and precedence[operators[-1]] >= precedence[token]):
                output.append(operators.pop())
            operators.append(token)

    while operators:
        output.append(operators.pop())

    return ' '.join(output)
