from __future__ import annotations
import json
import os
import re

"""New instruction set encoding (Sept 2025)

Format is determined by count of leading zeroes until first 1 bit:

1xxxxxxx                 : LDI #imm7
01dddsrc                 : MOV dst, src (d=dest bits, s=source bits)
001ooosrc                : Arithmetic (oo = op code, src = source reg)
00010src                 : AND src
00011iii                 : ADDI #imm3
00001ccc                 : Jump (condition ccc)
000001ii                 : SUBI #imm2
00000011                 : CRA (clear RA)
00000001                 : HLT
00000000 / 00000010      : NOP (both decoded as NOP, 00000010 reserved)

Destination register codes (MOV dest, src):
  RA=000 RD=001 MARL=010 MARH=011 PRL=100 PRH=101 ML=110 MH=111
Source register codes:
  RA=000 RD=001 ACC=010 CLR=011 PCL=100 PCH=101 ML=110 MH=111
Arithmetic op codes (oo): ADD=00 SUB=01 ADC=10 SBC=11
Jump condition codes (ccc): JMP=000 JEQ=001 JGT=010 JLT=011 JGE=100 JLE=101 JNE=110 JC=111
"""

# Load local config (only for special chars & keywords now)
def _load_local_config():
    base_dir = os.path.dirname(os.path.dirname(__file__))  # assemblerV2_python/
    cfg_path = os.path.join(base_dir, 'config', 'config.json')
    try:
        with open(cfg_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback minimal config
        return {
            "special_chars": {"comment": ";", "label": ":"},
            "keywords": {"constant": "const"}
        }

config = _load_local_config()

# Static tables for new encoding
DEST_REGS = {
    'RA': '000', 'RD': '001', 'MARL': '010', 'MARH': '011',
    'PRL': '100', 'PRH': '101', 'ML': '110', 'MH': '111'
}
SRC_REGS = {
    'RA': '000', 'RD': '001', 'ACC': '010', 'CLR': '011',
    'PCL': '100', 'PCH': '101', 'ML': '110', 'MH': '111'
}
ARITH_OPS = {'ADD': '00', 'SUB': '01', 'ADC': '10', 'SBC': '11'}
JUMP_CONDS = {'JMP': '000', 'JEQ': '001', 'JGT': '010', 'JLT': '011', 'JGE': '100', 'JLE': '101', 'JNE': '110', 'JC': '111'}

REV_DEST = {v: k for k, v in DEST_REGS.items()}
REV_SRC = {v: k for k, v in SRC_REGS.items()}
REV_ARITH = {v: k for k, v in ARITH_OPS.items()}
REV_JUMP = {v: k for k, v in JUMP_CONDS.items()}

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
        Supports:
         - CONST NAME VALUE
         - CONST NAME = VALUE
         - NAME EQU VALUE
        Matching is case-insensitive for keywords (CONST/EQU).
        """
        constants: dict[str, int] = {}
        const_kw_up = self.constant_keyword.upper()
        for line in lines:
            raw = line.strip()
            if not raw:
                continue
            up = raw.upper()

            # Pattern: CONST NAME [=] VALUE
            if up.startswith(const_kw_up):
                rest = raw[len(self.constant_keyword):].strip()
                if not rest:
                    continue
                # Split by '=' if present, else by whitespace
                if '=' in rest:
                    name_part, val_part = rest.split('=', 1)
                else:
                    parts = rest.split(None, 1)
                    if len(parts) != 2:
                        continue
                    name_part, val_part = parts[0], parts[1]
                const_name = name_part.strip().upper()
                const_value = self.to_decimal(val_part.strip())
                constants[const_name] = const_value
                continue

            # Pattern: NAME EQU VALUE
            m = re.match(r"^([A-Za-z_][\w]*)\s+EQU\s+(.+)$", raw, flags=re.IGNORECASE)
            if m:
                const_name = m.group(1).strip().upper()
                val_part = m.group(2).strip()
                const_value = self.to_decimal(val_part)
                constants[const_name] = const_value
                continue

        return constants

    def remove_constants(self, lines:list[str]) -> list[str]:
        """
        Removes constant-definition lines from a list of assembly lines.
        Handles both CONST ... and NAME EQU ... forms (case-insensitive).
        """
        cleaned_lines = []
        const_kw_up = self.constant_keyword.upper()
        for line in lines:
            raw = line.strip()
            up = raw.upper()
            if up.startswith(const_kw_up):
                continue
            if re.match(r"^[A-Za-z_][\w]*\s+EQU\s+.+$", raw, flags=re.IGNORECASE):
                continue
            cleaned_lines.append(line)
        return cleaned_lines
    
    # Legacy helper methods removed for new encoding (kept for backward compatibility if needed)
    
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
        if not line or not line.strip():
            return None

        # Split mnemonic and operands
        parts = line.strip().split(None, 1)
        mnemonic = parts[0].upper()
        operands_part = parts[1] if len(parts) > 1 else ''
        operands = []
        if operands_part:
            operands = [op.strip() for op in operands_part.split(',') if op.strip()]

        # Pseudo-instructions for memory low/high latches
        if mnemonic == 'STRL':
            # STRL src -> MOV ML, src
            if len(operands) != 1:
                raise ValueError(f"STRL syntax: STRL src -> got: {line}")
            src = operands[0].upper()
            if src not in SRC_REGS:
                raise ValueError(f"Unknown source register '{src}' in line: {line}")
            return '01' + DEST_REGS['ML'] + SRC_REGS[src]

        if mnemonic == 'STRH':
            # STRH src -> MOV MH, src
            if len(operands) != 1:
                raise ValueError(f"STRH syntax: STRH src -> got: {line}")
            src = operands[0].upper()
            if src not in SRC_REGS:
                raise ValueError(f"Unknown source register '{src}' in line: {line}")
            return '01' + DEST_REGS['MH'] + SRC_REGS[src]

        if mnemonic == 'LDRL':
            # LDRL dest -> MOV dest, ML
            if len(operands) != 1:
                raise ValueError(f"LDRL syntax: LDRL dest -> got: {line}")
            dest = operands[0].upper()
            if dest not in DEST_REGS:
                raise ValueError(f"Unknown destination register '{dest}' in line: {line}")
            return '01' + DEST_REGS[dest] + SRC_REGS['ML']

        if mnemonic == 'LDRH':
            # LDRH dest -> MOV dest, MH
            if len(operands) != 1:
                raise ValueError(f"LDRH syntax: LDRH dest -> got: {line}")
            dest = operands[0].upper()
            if dest not in DEST_REGS:
                raise ValueError(f"Unknown destination register '{dest}' in line: {line}")
            return '01' + DEST_REGS[dest] + SRC_REGS['MH']

        # LDI #imm7
        if mnemonic == 'LDI':
            if len(operands) != 1 or not operands[0].startswith('#'):
                raise ValueError(f"LDI syntax: LDI #imm7 -> got: {line}")
            imm = self.to_decimal(operands[0])
            if not 0 <= imm <= 127:
                raise ValueError(f"LDI immediate out of range (0..127): {imm}")
            return f"1{imm:07b}"

        # MOV dst, src
        if mnemonic == 'MOV':
            if len(operands) != 2:
                raise ValueError(f"MOV syntax: MOV dest, src -> got: {line}")
            dest, src = operands[0].upper(), operands[1].upper()
            if dest not in DEST_REGS:
                raise ValueError(f"Unknown destination register '{dest}' in line: {line}")
            if src not in SRC_REGS:
                raise ValueError(f"Unknown source register '{src}' in line: {line}")
            return '01' + DEST_REGS[dest] + SRC_REGS[src]

        # Arithmetic ops: ADD/SUB/ADC/SBC src
        if mnemonic in ARITH_OPS:
            if len(operands) != 1:
                raise ValueError(f"{mnemonic} syntax: {mnemonic} src -> got: {line}")
            src = operands[0].upper()
            if src not in SRC_REGS:
                raise ValueError(f"Unknown source register '{src}' in line: {line}")
            return '001' + ARITH_OPS[mnemonic] + SRC_REGS[src]

        # AND src
        if mnemonic == 'AND':
            if len(operands) != 1:
                raise ValueError(f"AND syntax: AND src -> got: {line}")
            src = operands[0].upper()
            if src not in SRC_REGS:
                raise ValueError(f"Unknown source register '{src}' in line: {line}")
            return '00010' + SRC_REGS[src]

        # ADDI #imm3
        if mnemonic == 'ADDI':
            if len(operands) != 1 or not operands[0].startswith('#'):
                raise ValueError(f"ADDI syntax: ADDI #imm3 -> got: {line}")
            imm = self.to_decimal(operands[0])
            if not 0 <= imm <= 7:
                raise ValueError(f"ADDI immediate out of range (0..7): {imm}")
            return '00011' + f"{imm:03b}"

        # SUBI #imm2 (2-bit immediate)
        if mnemonic == 'SUBI':
            if len(operands) != 1 or not operands[0].startswith('#'):
                raise ValueError(f"SUBI syntax: SUBI #imm2 -> got: {line}")
            imm = self.to_decimal(operands[0])
            if not 0 <= imm <= 3:
                raise ValueError(f"SUBI immediate out of range (0..3): {imm}")
            return '000001' + f"{imm:02b}"

        # Jumps
        if mnemonic in JUMP_CONDS:
            return '00001' + JUMP_CONDS[mnemonic]

        # Single-byte fixed encodings
        if mnemonic == 'CRA':
            return '00000011'
        if mnemonic == 'HLT':
            return '00000001'
        if mnemonic == 'NOP':
            return '00000000'

        raise ValueError(f"Unknown instruction: {mnemonic}")

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
        v = value.strip()
        # Allow optional immediate prefix (e.g., '#')
        if v.startswith(self.number_prefix):
            v = v[len(self.number_prefix):].strip()
        # Accept hex/bin with or without '#', case-insensitive
        low = v.lower()
        if low.startswith("0x"):
            return int(v, 16)
        if low.startswith("0b"):
            return int(v, 2)
        # Decimal (could be e.g., '10')
        return int(v, 10)
    
    def disassemble_instruction(self, instruction_byte:int|str):
        if instruction_byte is None:
            return 'NOP'
        b = int(instruction_byte) if isinstance(instruction_byte, str) else instruction_byte
        b &= 0xFF

        # LDI: bit7 = 1
        if b & 0x80:
            return f"LDI #{b & 0x7F}"

        bits = f"{b:08b}"

        # Fixed encodings first
        if bits == '00000000' or bits == '00000010':
            return 'NOP'
        if bits == '00000001':
            return 'HLT'
        if bits == '00000011':
            return 'CRA'

        # SUBI 000001ii
        if bits.startswith('000001'):
            imm = b & 0x03
            return f"SUBI #{imm}"

        # Jump 00001ccc
        if bits.startswith('00001'):
            cond = bits[5:8]
            return REV_JUMP.get(cond, f"J?{cond}")

        # ADDI 00011iii
        if bits.startswith('00011'):
            imm = b & 0x07
            return f"ADDI #{imm}"

        # AND 00010src
        if bits.startswith('00010'):
            src = bits[5:8]
            return f"AND {REV_SRC.get(src, '?')}"

        # Arithmetic 001ooosrc (oo = bits[3:5])
        if bits.startswith('001'):
            op = bits[3:5]
            src = bits[5:8]
            op_mnem = REV_ARITH.get(op, 'A?')
            return f"{op_mnem} {REV_SRC.get(src, '?')}"

        # MOV 01dddsrc
        if bits.startswith('01'):
            dest = bits[2:5]
            src = bits[5:8]
            return f"MOV {REV_DEST.get(dest, '?')}, {REV_SRC.get(src, '?')}"

        return f"UNK 0x{b:02X}"
    

    def convert_to_machine_code(self, raw_lines:list[str]):
        # Normalize to uppercase for mnemonics, registers, and symbol names
        clines = self.upper_lines(raw_lines)
        # Remove whitespace/comments on the normalized lines
        clines = self.remove_whitespaces_lines(clines)
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


