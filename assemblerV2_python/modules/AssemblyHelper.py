from __future__ import annotations
import json
import os

# Load config
config_path = "/home/ardac/projects/ArniComp-Support-Package/assembler/config/config.json"
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
            if line == "\n" or line.isspace() or line.startswith(self.comment_char) or line=="": 
                continue
            # Remove whitespace characters
            cleaned_line = ' '.join(line.split())
            # Remove comments
            if self.comment_char in cleaned_line:
                comment_pos = cleaned_line.find(self.comment_char)
                if comment_pos != -1:
                    cleaned_line = cleaned_line[:comment_pos]
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
                label_with_prefix = self.label_prefix + label
                if label_with_prefix in line:
                    line = line.replace(label_with_prefix, self.number_prefix+str(line_number))
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
                const_with_prefix = self.constant_prefix + const_name
                if const_with_prefix in line:
                    line = line.replace(const_with_prefix, self.number_prefix+str(const_value))
            changed_lines.append(line)
        return changed_lines
    
    def covert_to_binary(self, line:str):
        # Skip empty lines
        if not line or not line.strip():
            return None
            
        print(line)

        splitted_line = line.split()
        if len(splitted_line) == 1:
            inst_str = splitted_line[0].upper()
            args_list = []
        else:
            space_pos = line.find(" ")
            if space_pos != -1:
                inst_str = line[:space_pos].upper()
                args_list = line[space_pos:].replace(' ','').split(",")
            else:
                inst_str = line.upper()
                args_list = []
        
        # Skip if instruction is empty
        if not inst_str:
            return None
        
        if inst_str == "LDI":
            arg = self.to_decimal(args_list[0])
            return f"1{arg:07b}"
            
        print(f"Instruction: {inst_str}, Args: {args_list}")

        # Check if instruction exists in config
        if inst_str not in instructions:
            print(f"Unknown instruction: {inst_str}")
            return None

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
    
    def disassemble_instruction(self, instruction_byte):
        """
        Disassemble a single instruction byte to human-readable format
        
        Args:
            instruction_byte: The instruction byte to disassemble
            
        Returns:
            str: Human-readable instruction string
        """
        if instruction_byte is None:
            return "NOP"
        
        instruction = int(instruction_byte) if isinstance(instruction_byte, str) else instruction_byte
        
        # Check if it's an immediate instruction (LDI)
        if instruction & 0x80:  # MSB = 1 means LDI
            immediate_value = instruction & 0x7F  # Lower 7 bits
            return f"LDI #{immediate_value}"
        
        # Regular instruction format: 1 bit (0) + 4 bits opcode + 3 bits args
        opcode = (instruction >> 3) & 0x0F  # Bits 6-3 (4 bits)
        args = instruction & 0x07  # Bits 2-0 (3 bits)
        
        # Create reverse mapping from our config
        opcode_bin = f"{opcode:04b}"
        argcode_bin = f"{args:03b}"
        
        # Find instruction by opcode and argcode combination
        # First pass: Look for exact opcode+argcode matches
        for inst_name, inst_config in instructions.items():
            if inst_config.get("opcode_type") == "constant":
                config_opcode = inst_config.get("opcode")
                config_argcode = inst_config.get("argcode")
                
                # For instructions with constant opcode and argcode, match both exactly
                if (config_opcode == opcode_bin and 
                    config_argcode is not None and 
                    config_argcode == argcode_bin):
                    return inst_name
        
        # Second pass: Look for constant opcode instructions that use argcode for register parameters  
        for inst_name, inst_config in instructions.items():
            if inst_config.get("opcode_type") == "constant":
                config_opcode = inst_config.get("opcode")
                argcode_type = inst_config.get("argcode_type")
                
                # Match instructions with constant opcode that use argcode for register selection
                if config_opcode == opcode_bin and argcode_type in ["out_reg", "in_reg"]:
                    # Found matching instruction, now decode arguments
                    if inst_name == "ADD" or inst_name == "SUB":
                        # These use register arguments in argcode
                        reg_map = {"000": "RA", "001": "RD", "110": "ACC"}
                        reg_name = reg_map.get(argcode_bin, f"#{args}")
                        return f"{inst_name} {reg_name}"
                    
                    elif inst_name in ["ADDI", "SUBI"]:
                        # These use immediate values
                        return f"{inst_name} #{args}"
                    
                    elif inst_name in ["STRL", "STRH"]:
                        # These use register arguments - STRL/STRH dst <- src format
                        reg_map = {"000": "RA", "001": "RD", "110": "ACC"}
                        reg_name = reg_map.get(argcode_bin, f"#{args}")
                        return f"{inst_name} {reg_name}"
                    
                    elif inst_name in ["LDRL", "LDRH"]:
                        # These use register arguments - LDRL/LDRH dst <- memory format
                        reg_map = {"000": "RA", "001": "RD", "110": "ACC"}
                        reg_name = reg_map.get(argcode_bin, f"#{args}")
                        return f"{inst_name} {reg_name}"
                    
                    elif inst_name == "OUT":
                        # OUT uses register arguments
                        reg_map = {"000": "RA", "001": "RD", "110": "ACC"}
                        reg_name = reg_map.get(argcode_bin, f"#{args}")
                        return f"{inst_name} {reg_name}"
                        
                    elif inst_name == "IN":
                        # IN uses register arguments
                        reg_map = {"000": "RA", "001": "RD", "110": "ACC"}
                        reg_name = reg_map.get(argcode_bin, f"#{args}")
                        return f"{inst_name} {reg_name}"
                    
                    else:
                        return inst_name
        
        # Third pass: Look for opcode_type="in_reg" instructions (opcode encodes source register)
        for inst_name, inst_config in instructions.items():
            opcode_type = inst_config.get("opcode_type")
            argcode_type = inst_config.get("argcode_type")
            config_argcode = inst_config.get("argcode")
            
            if opcode_type == "in_reg" and config_argcode is not None:
                # Match instructions like LDRL, LDRH that have opcode_type="in_reg" and fixed argcode
                if config_argcode == argcode_bin:
                    # Found exact argcode match for in_reg instruction
                    if inst_name in ["LDRL", "LDRH"]:
                        # For LDRL/LDRH, the opcode field contains the register
                        reg_map = {
                            "1000": "RA", "1001": "RD", "1010": "ML", "1011": "MH",
                            "1100": "PRL", "1101": "PRH", "1110": "MARL", "1111": "P",
                            "0001": "MARH", "0110": "ACC"
                        }
                        reg_name = reg_map.get(opcode_bin, f"0x{instruction:02X}")
                        return f"{inst_name} {reg_name}"
                    
                    elif inst_name == "IN":
                        # IN also uses opcode for register
                        reg_map = {
                            "1000": "RA", "1001": "RD", "1010": "ML", "1011": "MH",
                            "1100": "PRL", "1101": "PRH", "1110": "MARL", "1111": "P",
                            "0001": "MARH", "0110": "ACC"
                        }
                        reg_name = reg_map.get(opcode_bin, f"0x{instruction:02X}")
                        return f"{inst_name} {reg_name}"
                    
                    else:
                        return inst_name

        # Fourth pass: Look for opcode-only matches (instructions with argcode=None)
        for inst_name, inst_config in instructions.items():
            if inst_config.get("opcode_type") == "constant":
                config_opcode = inst_config.get("opcode")
                config_argcode = inst_config.get("argcode")
                
                # For instructions with only constant opcode (no argcode defined)
                if config_opcode == opcode_bin and config_argcode is None:
                    return inst_name
            
        # Fifth pass: Handle MOV separately (it uses opcode for source register)
        for inst_name, inst_config in instructions.items():
            if inst_name == "MOV":
                # MOV has opcode_type="in_reg" and argcode_type="out_reg"
                # This means the opcode field encodes the source register
                # and the argcode field encodes the destination register
                
                # Source register mapping (from opcode_types.in_reg + missing mappings)
                src_regs = {
                    "1000": "RA", "1001": "RD", "1010": "ML", "1011": "MH",
                    "1100": "PRL", "1101": "PRH", "1110": "MARL", "1111": "P",
                    "0001": "MARH", "0110": "ACC", "0111": "RA"  # Add missing 0111->RA mapping
                }
                
                # Destination register mapping (from argcode_types.out_reg)
                dst_regs = {
                    "000": "RA", "001": "RD", "010": "ML", "011": "MH",
                    "100": "PCL", "101": "PCH", "110": "ACC", "111": "P"
                }
                
                src_reg = src_regs.get(opcode_bin, None)
                dst_reg = dst_regs.get(argcode_bin, None)
                
                if src_reg and dst_reg:
                    # MOV syntax analysis:
                    # Assembly: "mov marl, ra" encodes as 0x70
                    # 0x70 = 01110000: opcode=0111, argcode=000
                    # Our mapping: opcode=0111->unknown, argcode=000->RA
                    # But user expects: MOV MARL, RA (MARL <- RA)
                    # This suggests: MOV source, destination format
                    return f"MOV {src_reg}, {dst_reg}"
                    
            # Handle other instructions with variable opcodes
            elif inst_config.get("opcode_type") == "in_reg":
                # Instructions like LDRL, LDRH, IN where opcode encodes a register
                reg_map = {
                    "1000": "RA", "1001": "RD", "1010": "ML", "1011": "MH",
                    "1100": "PRL", "1101": "PRH", "1110": "MARL", "1111": "P",
                    "0001": "MARH"
                }
                
                reg_name = reg_map.get(opcode_bin, None)
                if reg_name:
                    return f"{inst_name} {reg_name}"
        
        return f"UNK 0x{instruction:02X}"
    

    def convert_to_machine_code(self, raw_lines:list[str]):
        clines = self.upper_lines(raw_lines)
        clines = self.remove_whitespaces_lines(raw_lines)
        print(f"Cleaned lines: {clines}")
        constants = self.get_constants(clines)
        print(f"Constants found: {constants}")
        clines = self.remove_constants(clines)
        labels = self.get_labels(clines)
        clines = self.remove_labels(clines)
        print(f"Labels found: {labels}")
        clines = self.change_labels(clines, labels)
        clines = self.change_constants(clines, constants)

        blines = self.convert_to_binary_lines(clines)

        lines_to_write_bin = [f"{line}\n" for line in blines]
        return lines_to_write_bin, labels, constants
          
class Assembler:
    def __init__(self):
        pass


