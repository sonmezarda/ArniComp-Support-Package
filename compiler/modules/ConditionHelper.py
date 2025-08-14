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
            if_statement = self.get_if()
            if_lines = if_statement.get_lines()
            processed_lines = []
            for i, line in enumerate(if_lines):
                print(f"Processing if line {i}: '{line}'")
                if isinstance(line, IfElseClause):
                    line.apply_to_all_lines(func)
                    processed_lines.append(line)
                elif isinstance(line, str):
                    # String satırları Command listesine dönüştür
                    commands = func([line])
                    processed_lines.extend(commands)
                else:
                    processed_lines.append(line)
            if_statement.lines = processed_lines

        if 'elif' in self.clause:
            for elif_clause in self.get_elif():
                elif_lines = elif_clause.get_lines()
                processed_lines = []
                for line in elif_lines:
                    if isinstance(line, IfElseClause):
                        line.apply_to_all_lines(func)
                        processed_lines.append(line)
                    elif isinstance(line, str):
                        commands = func([line])
                        processed_lines.extend(commands)
                    else:
                        processed_lines.append(line)
                elif_clause.lines = processed_lines
        
        if 'else' in self.clause:
            else_statement = self.get_else()
            else_lines = else_statement.get_lines()
            processed_lines = []
            for line in else_lines:
                if isinstance(line, IfElseClause):
                    line.apply_to_all_lines(func)
                    processed_lines.append(line)
                elif isinstance(line, str):
                    commands = func([line])
                    processed_lines.extend(commands)
                else:
                    processed_lines.append(line)
            else_statement.lines = processed_lines

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
    def group_nested_if_else(lines):
        def parse_block(iter_lines):
            result = []
            try:
                while True:
                    line = next(iter_lines).strip()
                    if line.startswith("if "):
                        # nested blok olabilir — blok gövdesini listele
                        header = line
                        nested = [header]
                        nested.extend(parse_block(iter_lines))
                        result.append(nested)
                    elif line.startswith("elif ") or line == "else":
                        result.append(line)
                    elif line == "endif":
                        return result
                    else:
                        result.append(line)
            except StopIteration:
                return result

        return parse_block(iter(lines))[0]



    @staticmethod
    def parse_from_lines(lines: list[str | list]) -> IfElseClause:
        
        clause = IfElseClause()
        current_branch = None  # Şu anda hangi blok üzerinde çalışıyoruz (if/elif/else)

        for i, item in enumerate(lines):
            if isinstance(item, list):
                # Liste içindeyse bu nested bir if bloğudur
                nested_clause = IfElseClause.parse_from_lines(item)
                if current_branch is None:
                    raise ValueError(f"Nested if must come after a condition (if/elif/else), but got nested block at index {i} with no active branch.")
                current_branch.add_line(nested_clause)

            elif isinstance(item, str):
                stripped = item.strip()

                if stripped.startswith("if "):
                    condition = stripped[3:].strip()
                    if clause.is_contains_if():
                        raise ValueError(f"Multiple top-level 'if' clauses detected! Already have: {clause.get_if().condition}, tried to add: {condition}")
                    current_branch = clause.add_if(condition)

                elif stripped.startswith("elif "):
                    condition = stripped[5:].strip()
                    current_branch = clause.add_elif(condition)

                elif stripped == "else":
                    current_branch = clause.add_else()

                else:
                    if current_branch is None:
                        raise ValueError(f"Unexpected line outside of any condition block: {item}")
                    current_branch.add_line(stripped)

            else:
                raise TypeError(f"Unexpected item type at index {i}: {type(item)}")

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

class WhileClause(GroupObject):
    def __init__(self, condition: str):
        self.condition: Condition = Condition(condition)
        self.lines: list[str | GroupObject] = []

    def add_line(self, line: str | GroupObject) -> None:
        self.lines.append(line)

    def get_lines(self) -> list[str | GroupObject]:
        return self.lines

    def apply_to_all_lines(self, func: callable) -> None:
        processed: list = []
        for line in self.lines:
            if isinstance(line, IfElseClause) or isinstance(line, WhileClause):
                line.apply_to_all_lines(func)
                processed.append(line)
            elif isinstance(line, str):
                cmds = func([line])
                processed.extend(cmds)
            else:
                processed.append(line)
        self.lines = processed

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

    def __str__(self) -> str:
        return f"Condition(type= {self.type}, parts={self.parts})"
    
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
        "   if x < 10",
        "        do_something_else2()",
        "           if y == 0",
        "               do_something_special()",
        "           endif",
        "    else",
        "        do_something_else3()",
        "   endif",
        "elif x < 5",
        "    do_something_else()",
        "    do_another_thing()",
        "elif x < 5",
        "    if y == 0",
        "        do_something_special()",
        "    endif",
        "    do_something_else()",
        "    do_another_thing()",
        "else",
        "    do_default()",
        "endif"
    ]
    
    lines = [line.strip() for line in lines if line.strip()]  
    glines = IfElseClause.group_nested_if_else(lines)
    parsed = IfElseClause.parse_from_lines(glines)
    print(parsed.get_if().lines[1].get_if().lines[1].get_if().lines)

