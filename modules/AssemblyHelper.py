
import json
import os

# Load config
config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.json')
with open(config_path, 'r') as f:
    config = json.load(f)

instructions = config['instructions']
opcode_types = config['opcode_types']
argcode_types = config['argcode_types']

class AssemblyHelper:
    def __init__(self, comment_char:str, label_char:str, constant_keyword:str, number_prefix:str, constant_prefix:str, label_prefix:str):
        """
        Initializes the AssemblyHelper with a comment character.
        
        Args:
            comment_char (str): The character that indicates the start of a comment in the file.
        """
        self.comment_char = comment_char
        self.label_char = label_char
        self.constant_keyword = constant_keyword
        self.number_prefix = number_prefix
        self.constant_prefix = constant_prefix
        self.label_prefix = label_prefix

    def upper_lines(self, lines:list[str]) -> list[str]:
        """
        Converts all lines in a list to uppercase.
        
        Args:
            lines (list[str]): The list of lines to be converted.
        
        Returns:
            list[str]: A new list with all lines converted to uppercase.
        """
        return [line.upper() for line in lines]
    
    def get_file_extension(self, filename:str) -> tuple[str, str]:
        splitted = filename.split('.')
        return (splitted[0], splitted[1]) if len(splitted) > 1 else (splitted[0], '')
    
    def remove_whitespaces_lines(self, lines:list[str]) -> list[str]:
        """
        Removes all whitespace characters from a list of lines.
        
        Args:
            lines (list[str]): The list of lines to be cleaned.
        
        Returns:
            list[str]: A new list with whitespace characters removed.
        """
        cleaned_lines = []
        for line in lines:
            if line == "\n" or line.isspace() or line.startswith(self.comment_char): 
                continue
            # Remove whitespace characters
            cleaned_line = ' '.join(line.split())
            # Remove comments
            if self.comment_char in cleaned_line:
                cleaned_line = cleaned_line[:cleaned_line.index(self.comment_char)]
            cleaned_lines.append(cleaned_line)
        return cleaned_lines

    def get_labels(self, lines:list[str]) -> dict[str, int]:
        """
        Extracts labels from a list of assembly lines.
        
        Args:
            lines (list[str]): The list of assembly lines.
        
        Returns:
            dict[str, int]: A dictionary with labels as keys and their line numbers as values.
        """
        labels = {}
        label_count = 0
        for i, line in enumerate(lines):
            if line.endswith(self.label_char):
                label_name = line[:-1].strip()
                label_index = i - label_count
                label_count += 1
                labels[label_name] = label_index
        return labels
    
    def remove_labels(self, lines:list[str]) -> list[str]:
        """
        Removes labels from a list of assembly lines.
        
        Args:
            lines (list[str]): The list of assembly lines.
        
        Returns:
            list[str]: A new list with labels removed.
        """
        cleaned_lines = []
        for line in lines:
            if line.endswith(self.label_char):
                continue
            cleaned_lines.append(line)
        return cleaned_lines

    def get_constants(self, lines:list[str]) -> dict[str, int]:
        """
        Extracts constants from a list of assembly lines.
        
        Args:
            lines (list[str]): The list of assembly lines.
        
        Returns:
            dict[str, int]: A dictionary with constant names as keys and their values as integers.
        """
        constants = {}
        for line in lines:
            if line.startswith(self.constant_keyword):
                line = line.replace(self.constant_keyword, '', 1)
                line = line.strip()
                parts = line.split('=')
                if len(parts) == 2:
                    const_name = parts[0].strip()
                    const_value = self.to_decimal(parts[1].strip())
                    constants[const_name] = const_value
        return constants

    def remove_constants(self, lines:list[str]) -> list[str]:
        """
        Removes constants from a list of assembly lines.
        
        Args:
            lines (list[str]): The list of assembly lines.
        
        Returns:
            list[str]: A new list with constants removed.
        """
        cleaned_lines = []
        for line in lines:
            if line.startswith(self.constant_keyword):
                continue
            cleaned_lines.append(line)
        return cleaned_lines
    
    def convert_to_machine_code(self, lines:list[str]) -> int:
        pass
            
    def _select_opcode(self, instruction:dict[str, str], args:list[str]) -> str:
        opcode_type = instruction["opcode_type"]
        opcode = None
        if opcode_type == "in_reg":
            opcode_order = instruction["opcode_arg_order"]
            opcode = opcode_types[opcode_type][args[opcode_order]]
        elif opcode_type == "constant":
            opcode = instruction["opcode"]
        return opcode

    def _select_arg_code(self, instruction:dict[str, str], args:list[str]) -> str:
        arg_type = instruction["argcode_type"]
        argcode = None
        if arg_type == "out_reg":
            argcode_order = instruction["argcode_arg_order"]
            argcode = argcode_types[arg_type][args[argcode_order]]
        elif arg_type == "constant":
            argcode = instruction["argcode"]
        elif arg_type == "number":
            argcode_order = instruction["argcode_arg_order"]
            argcode = self.to_decimal(args[argcode_order])
            argcode = f"{argcode:03b}"  # Convert to 3-bit binary
        return argcode

    @staticmethod
    def _merge_instruction(im7, opcode, arg_code):
        return im7 + opcode + arg_code
    
    def change_labels(self, lines:list[str], labels:dict[str, int]) -> list[str]:
        """
        Replaces labels in assembly lines with their corresponding line numbers.
        
        Args:
            lines (list[str]): The list of assembly lines.
            labels (dict[str, int]): A dictionary with labels as keys and their line numbers as values.
        
        Returns:
            list[str]: A new list with labels replaced by their corresponding line numbers.
        """
        changed_lines = []
        for line in lines:
            for label, line_number in labels.items():
                if label in line:
                    line = line.replace(self.label_prefix+label, self.number_prefix+str(line_number))
            changed_lines.append(line)
        return changed_lines
    
    def change_constants(self, lines:list[str], constants:dict[str, int]) -> list[str]:
        """
        Replaces constants in assembly lines with their corresponding values.
        
        Args:
            lines (list[str]): The list of assembly lines.
            constants (dict[str, int]): A dictionary with constant names as keys and their values as integers.
        
        Returns:
            list[str]: A new list with constants replaced by their corresponding values.
        """
        changed_lines = []
        for line in lines:
            for const_name, const_value in constants.items():
                if const_name in line:
                    line = line.replace(self.constant_prefix+const_name, self.number_prefix+str(const_value))
            changed_lines.append(line)
        return changed_lines
    
    def covert_to_binary(self, line:str):
        print(line)

        splitted_line = line.split()
        if len(splitted_line) == 1:
            inst_str = splitted_line[0].upper()
            args_list = []
        else:
            inst_str = line[:line.index(" ")].upper()
            args_list = line[line.index(" "):].replace(' ','').split(",")
        
        if inst_str == "LDI":
            arg = self.to_decimal(args_list[0])
            return f"1{arg:07b}"
            
        print(f"Instruction: {inst_str}, Args: {args_list}")

        opcode =  self._select_opcode(instructions[inst_str], args_list)
        arg_code = self._select_arg_code(instructions[inst_str], args_list)
        print(f"Opcode: {opcode}, Arg Code: {arg_code}")
        ins = self._merge_instruction('0', opcode, arg_code)
        print(ins)
        return ins if ins else None

    def convert_to_binary_lines(self, lines:list[str]) -> list[str]:
        """
        Converts a list of assembly lines to binary machine code.
        
        Args:
            lines (list[str]): The list of assembly lines.
        
        Returns:
            list[str]: A new list with each line converted to binary machine code.
        """
        binary_lines = []
        for line in lines:
            binary_line = self.covert_to_binary(line)
            if binary_line:
                binary_lines.append(binary_line)
        return binary_lines
    
    def to_decimal(self, value:str) -> int:
        if value.startswith(self.number_prefix):
            value = value[len(self.number_prefix):]
            if value.startswith("0x"):
                return int(value[2:], 16)
            elif value.startswith("0b"):
                return int(value[2:], 2)
            else:
                return int(value)
        else:
            return int(value)
          
class Assembler:
    def __init__(self):
        pass


