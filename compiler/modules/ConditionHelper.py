from __future__ import annotations

from enum import StrEnum

class GroupObject:
    pass

class IfElseClause(GroupObject):
    def __init__(self):
        self.clause = {}

    def add_if(self, condition: str) -> IfStatement:
        if 'if' in self.clause:
            raise ValueError("If clause already exists. Use 'elif' or 'else' for additional conditions.")
        
        new_if = IfStatement(condition)
        self.clause['if'] = new_if
        return new_if    
    
    def add_elif(self, condition: str) -> IfStatement:
        if 'if' not in self.clause:
            raise ValueError("No 'if' clause exists. Use 'add_if' to define the initial condition.")
        if 'else' in self.clause:
            raise ValueError("Cannot add 'elif' after 'else'. Use 'add_if' or 'add_elif' before adding 'else'.")
        
        if 'elif' not in self.clause:
            self.clause['elif'] = []
        
        new_elif = IfStatement(condition)

        self.clause['elif'].append(new_elif)
        return new_elif
    
    def add_else(self) -> ElseStatement:
        if 'else' in self.clause:
            raise ValueError("Else clause already exists.")
        new_else = ElseStatement()
        self.clause['else'] = new_else
        return new_else
    
    def get_if(self) -> IfStatement | None:
        return self.clause.get('if', None)
    
    def get_elif(self) -> list[IfStatement]:
        return self.clause.get('elif', [])
    
    def get_else(self) -> ElseStatement | None:
        return self.clause.get('else', None)
    
    def is_contains_if(self) -> bool:
        return self.get_if() is not None
    
    def is_contains_elif(self) -> bool:
        return len(self.get_elif()) > 0
    
    def is_contains_else(self) -> bool:
        return self.get_else() is not None
    
    def apply_to_all_lines(self, func: callable) -> None:
        if 'if' in self.clause:
            new_lines = func(self.get_if().get_lines())
            self.get_if().lines = new_lines

        if 'elif' in self.clause:
            for elif_clause in self.get_elif():
                new_lines=func(elif_clause.get_lines())
                elif_clause.lines = new_lines
        
        if 'else' in self.clause:
            new_lines = func(self.get_else().get_lines())
            self.get_else().lines = new_lines

    def __repr__(self) -> str:
        result = []
        if 'if' in self.clause:
            result.append(f"if {self.clause['if'].condition}")

            result.extend(['\t'+str(line) for line in self.clause['if'].get_lines()])
        
        if 'elif' in self.clause:
            for elif_clause in self.clause['elif']:
                result.append(f"elif {elif_clause.condition}")
                result.extend(['\t'+str(line) for line in elif_clause.get_lines()])
        
        if 'else' in self.clause:
            result.append("else")
            result.extend(['\t'+str(line) for line in self.clause['else'].get_lines()])
        
        return '\n'.join(result)
    

    @staticmethod
    def parse_from_lines(lines: list[str]) -> IfElseClause:
        clause = IfElseClause()
        current_if = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('if '):
                condition = line[3:].strip()
                current_if = clause.add_if(condition)
            elif line.startswith('elif '):
                condition = line[5:].strip()
                current_if = clause.add_elif(condition)
            elif line.startswith('else'):
                current_if = clause.add_else()
            else:
                if current_if is not None:
                    current_if.add_line(line)
        
        return clause

class Statement:
    def __init__(self):
        self.lines = []
    
    def add_line(self, line: str) -> None:
        self.lines.append(line)

    def get_lines(self) -> list[str]:
        return self.lines

    
class IfStatement(Statement):
    def __init__(self, condition:str):
        self.condition:Condition = Condition(condition)
        super().__init__()
    

class ElseStatement(Statement):
    def __init__(self):
        super().__init__()

class ConditionTypes(StrEnum):
    EQUAL = "=="
    NOT_EQUAL = "!="
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    

class Condition:
    def __init__(self, condition_str: str):
        self.condition_str = condition_str
        self.type: ConditionTypes | None = None
        self.parts: tuple[str, str] | None = None
        self.__set_type()
        self.parts = self.split_parts()

    def get_str(self) -> str:
        return self.condition_str

    
    def __set_type(self) -> None:
        for cond_type in ConditionTypes:
            if cond_type.value in self.condition_str:
                self.type = cond_type
                return
        raise ValueError(f"Unknown condition type in '{self.condition_str}'")

    def split_parts(self) -> tuple[str, str]:
        if self.type is None:
            raise ValueError("Condition type is not set. Call __set_type() first.")
        
        parts = self.condition_str.split(self.type.value)
        if len(parts) != 2:
            raise ValueError(f"Invalid condition format: '{self.condition_str}'")
        return parts[0].strip(), parts[1].strip()

class ConditionChain:
    def __init__(self):
        raise NotImplementedError("ConditionChain is not implemented yet.")

if __name__ == '__main__':
    # Example usage
    lines = [
        "if x > 10",
        "    do_something()",
        "elif x < 5",
        "    do_something_else()",
        "    do_another_thing()",
        "elif x < 5",
        "    do_something_else()",
        "    do_another_thing()",
        "else",
        "    do_default()"
    ]
    
    clause = IfElseClause.parse_from_lines(lines)
    

    print(clause)