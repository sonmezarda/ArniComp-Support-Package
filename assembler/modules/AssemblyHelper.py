"""
AssemblyHelper: A clean, modular assembler for the custom ISA
Handles assembly language parsing, validation, and binary code generation
"""

from __future__ import annotations
from dataclasses import dataclass, field
import json
import os
import re
from typing import Dict, List, Tuple, Optional

# Load configuration
config_path = "../assembler/config/config.json"

with open(config_path, 'r') as f:
    config = json.load(f)

# Extract configuration sections
INSTRUCTIONS = config['instructions']
DESTINATIONS = config['destinations']
SOURCES = config['sources']
COMMENT_CHAR = config['special_chars']['comment']
LABEL_CHAR = config['special_chars']['label']
CONSTANT_KEYWORD = config['keywords']['constant']


@dataclass(frozen=True)
class LabelReference:
    """Represents a label-based LDI operand."""
    source_text: str
    label_name: str
    part: str
    address: int
    byte_value: int

    @property
    def encoded_immediate(self) -> int:
        """LDI can only encode the low 7 bits directly."""
        return self.byte_value & 0x7F


@dataclass
class ParsedLine:
    """Parsed source line with optional label metadata."""
    line_number: int
    raw_line: str
    instruction: str
    args: List[str]
    label_ref: Optional[LabelReference] = None


@dataclass
class LabelLoadSegment:
    """Tracks how one label byte is loaded into RA and consumed."""
    reference: LabelReference
    smsbra_used: bool = False
    mov_dests: set[str] = field(default_factory=set)


class InstructionEncoder:
    """Handles encoding of instructions to binary format"""
    
    @staticmethod
    def encode_ldi(immediate: int) -> str:
        """Encode LDI instruction: LDI #imm7"""
        if not (0 <= immediate <= 127):
            raise ValueError(f"LDI immediate value {immediate} out of range (0-127)")
        return f"1{immediate:07b}"
    
    @staticmethod
    def encode_mov(dest: str, src: str) -> str:
        """Encode MOV instruction: MOV dest, src
        Format: 0 1 [A1 A2 J=source] [S2 S1 S0=dest]
        Based on instruction table:
        - Row 3: Move From RA -> 01 000 [D2D1D0]
        - Row 5: Move From RD -> 01 001 [D2D1D0]
        - Row 7: Move From RB -> 01 010 [D2D1D0]
        - Row 9: Move From ACC -> 01 011 [D2D1D0]
        - Row 11: Move From PCL -> 01 100 [D2D1D0]
        - Row 12: Move From PCH -> 01 101 [D2D1D0]
        - Row 13: Move From Memory -> 01 111 [D2D1D0]
        """
        dest_upper = dest.upper()
        src_upper = src.upper()
        
        # Validate forbidden combinations
        forbidden = [("RA", "RA"), ("RD", "RD"), ("RB", "RB"), ("M", "M")]
        if (dest_upper, src_upper) in forbidden:
            raise ValueError(f"MOV {dest}, {src} is forbidden (same source and destination)")
        
        # Get encodings
        if dest_upper not in DESTINATIONS:
            raise ValueError(f"Invalid destination register: {dest}")
        if src_upper not in SOURCES:
            raise ValueError(f"Invalid source register: {src}")
            
        dest_bits = DESTINATIONS[dest_upper]
        src_bits = SOURCES[src_upper]
        
        # CORRECT FORMAT: 01 [source] [dest]
        return f"01{src_bits}{dest_bits}"
    
    @staticmethod
    def encode_not(src: str) -> str:
        """Encode NOT instruction
        Allowed sources: RA, RB, ACC, RD, M
        Based on instruction table:
        - Row 4: NOT RA  -> 0 1 0 0 0 0 0 0 = 01000000
        - Row 6: NOT RD  -> 0 1 0 0 1 0 0 1 = 01001001
        - Row 8: NOT ACC -> 0 1 0 1 0 0 1 0 = 01010010
        - Row 14: NOT M  -> 0 1 1 1 1 1 1 1 = 01111111
        - Row 31: NOT RB -> 0 0 0 0 0 1 0 0 = 00000100
        """
        src_upper = src.upper()
        allowed = ["RA", "RB", "ACC", "RD", "M"]
        
        if src_upper not in allowed:
            raise ValueError(f"NOT instruction only supports {allowed}, got {src}")
        
        encodings = {
            "RA": "01000000",   # Row 4:  NOT RA
            "RD": "01001001",   # Row 6:  NOT RD (düzeltildi: 01001001, 01001000 değil)
            "ACC": "01010010",  # Row 8:  NOT ACC
            "M": "01111111",    # Row 14: NOT M
            "RB": "00000100"    # Row 31: NOT RB (düzeltildi: 00000100, 01010000 değil)
        }
        
        return encodings[src_upper]
    
    @staticmethod
    def encode_arithmetic(operation: str, src: str) -> str:
        """Encode ADD, SUB, ADC, SBC, AND instructions
        All sources allowed: RA, RD, RB, ACC, PCL, PCH, M
        Format based on instruction table
        """
        src_upper = src.upper()
        
        if src_upper not in SOURCES:
            raise ValueError(f"Invalid source for {operation}: {src}")
        
        src_bits = SOURCES[src_upper]
        
        # Based on instruction table
        # ADD (row 15): 0 0 0 0 1 S2 S1 S0
        # SUB (row 17): 0 0 0 1 0 S2 S1 S0  
        # ADC (row 19): 0 0 0 1 1 S2 S1 S0
        # SBC (row 21): 0 0 1 0 0 S2 S1 S0
        # AND (row 23): 0 0 1 0 1 S2 S1 S0
        
        op_prefixes = {
            "ADD": "00001",
            "SUB": "00010",
            "ADC": "00011",
            "SBC": "00100",
            "AND": "00101"
        }
        
        if operation.upper() not in op_prefixes:
            raise ValueError(f"Unknown arithmetic operation: {operation}")
        
        return f"{op_prefixes[operation.upper()]}{src_bits}"
    
    @staticmethod
    def encode_xor(src: str) -> str:
        """Encode XOR instruction
        Allowed sources: RA, RB, RD, ACC, M
        """
        src_upper = src.upper()
        allowed = ["RA", "RB", "RD", "ACC", "M"]
        
        if src_upper not in allowed:
            raise ValueError(f"XOR instruction only supports {allowed}, got {src}")
        
        # Based on instruction table
        # Row 16: XOR RA -> 0 0 0 0 1 1 0 0
        # Row 18: XOR RB -> 0 0 0 1 0 1 0 0
        # Row 20: XOR ACC -> 0 0 0 1 1 0 1 0
        # Row 22: XOR M -> 0 0 1 0 0 1 0 0
        # Row 24: XOR RD -> 0 0 1 0 1 1 0 0
        
        encodings = {
            "RA": "00001100",
            "RB": "00010100",
            "RD": "00101100",
            "ACC": "00011010",
            "M": "00100100"
        }
        
        return encodings[src_upper]
    
    @staticmethod
    def encode_immediate_arithmetic(operation: str, immediate: int) -> str:
        """Encode ADDI/SUBI with 3-bit immediate
        Format: 0 0 1 1 J IM2 IM1 IM0
        ADDI: J=0, SUBI: J=1
        """
        if not (0 <= immediate <= 7):
            raise ValueError(f"{operation} immediate value {immediate} out of range (0-7)")
        
        if operation.upper() == "ADDI":
            return f"00110{immediate:03b}"
        elif operation.upper() == "SUBI":
            return f"00111{immediate:03b}"
        else:
            raise ValueError(f"Unknown immediate operation: {operation}")
    
    @staticmethod
    def encode_jump(condition: str) -> str:
        """Encode jump instructions
        Format: 0 1 1 0 0 JS2 JS1 JS0
        Conditions map to last 3 bits
        """
        conditions = {
            "JMP": "000",
            "JEQ": "001",
            "JGT": "010",
            "JLT": "011",
            "JGE": "100",
            "JLE": "101",
            "JNE": "110",
            "JC": "111"
        }
        
        cond_upper = condition.upper()
        if cond_upper not in conditions:
            raise ValueError(f"Unknown jump condition: {condition}")
        
        return f"01100{conditions[cond_upper]}"
    
    @staticmethod
    def encode_cmp(src: str) -> str:
        """Encode CMP instruction
        Allowed sources: RA, M, ACC
        """
        src_upper = src.upper()
        allowed = ["RA", "M", "ACC"]
        
        if src_upper not in allowed:
            raise ValueError(f"CMP instruction only supports {allowed}, got {src}")
        
        # Based on instruction table
        # Row 32: CMP RA and RD -> 0 0 0 0 0 1 0 1
        # Row 33: CMP M and RD -> 0 0 0 0 0 1 1 0
        # Row 34: CMP ACC and RD -> 0 0 0 0 0 1 1 1
        
        encodings = {
            "RA": "00000101",
            "M": "00000110",
            "ACC": "00000111"
        }
        
        return encodings[src_upper]
    
    @staticmethod
    def encode_special(instruction: str) -> str:
        """Encode special instructions: NOP, HLT, SMSBRA, INX"""
        specials = {
            "NOP": "00000000",
            "HLT": "00000001",
            "SMSBRA": "00000010",
            "INX": "00000011"
        }
        
        inst_upper = instruction.upper()
        if inst_upper not in specials:
            raise ValueError(f"Unknown special instruction: {instruction}")
        
        return specials[inst_upper]


class AssemblyHelper:
    """Main assembler class for parsing and converting assembly to machine code"""
    
    def __init__(self, comment_char: str = ';', label_char: str = ':', 
                 constant_keyword: str = 'equ', number_prefix: str = '#',
                 constant_prefix: str = '$', label_prefix: str = '@'):
        self.comment_char = comment_char
        self.label_char = label_char
        self.constant_keyword = constant_keyword.lower()
        self.number_prefix = number_prefix
        self.constant_prefix = constant_prefix
        self.label_prefix = label_prefix
        self.encoder = InstructionEncoder()
        self.last_warnings: List[str] = []
    
    def to_decimal(self, value: str) -> int:
        """Convert various number formats to decimal
        Supports: #0x10, #0b1010, #10, 0x10, 0b1010, 10
        """
        value = value.strip()
        
        # Remove number prefix if present
        if value.startswith(self.number_prefix):
            value = value[len(self.number_prefix):]
        
        # Parse different number formats
        if value.startswith("0x") or value.startswith("0X"):
            return int(value[2:], 16)
        elif value.startswith("0b") or value.startswith("0B"):
            return int(value[2:], 2)
        else:
            return int(value)
    
    def clean_lines(self, lines: List[str]) -> List[str]:
        """Remove comments, whitespace, and empty lines"""
        cleaned = []
        
        for line in lines:
            # Remove comments
            if self.comment_char in line:
                line = line[:line.index(self.comment_char)]
            
            # Strip whitespace
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            cleaned.append(line)
        
        return cleaned
    
    def extract_constants(self, lines: List[str]) -> Tuple[Dict[str, int], List[str]]:
        """Extract EQU constant definitions
        Format: equ NAME value
        """
        constants = {}
        remaining_lines = []
        
        for line in lines:
            parts = line.split(None, 2)  # Split on whitespace, max 3 parts
            
            if parts and parts[0].lower() == self.constant_keyword:
                if len(parts) < 3:
                    raise ValueError(f"Invalid constant definition: {line}")
                
                const_name = parts[1].upper()
                const_value = self.to_decimal(parts[2])
                constants[const_name] = const_value
            else:
                remaining_lines.append(line)
        
        return constants, remaining_lines
    
    def extract_labels(self, lines: List[str]) -> Tuple[Dict[str, int], List[str]]:
        """Extract labels and their line numbers
        Format: label:
        """
        labels = {}
        remaining_lines = []
        line_number = 0
        
        for line in lines:
            if line.endswith(self.label_char):
                # Extract label name
                label_name = line[:-1].strip().upper()
                labels[label_name] = line_number
            else:
                remaining_lines.append(line)
                line_number += 1
        
        return labels, remaining_lines
    
    def resolve_constants(self, lines: List[str], constants: Dict[str, int]) -> List[str]:
        """Replace constant references with their values
        $CONST is replaced with #value (adds # prefix for immediate values)
        """
        resolved = []
        
        for line in lines:
            # Replace all constant references
            for const_name, const_value in constants.items():
                const_ref = self.constant_prefix + const_name
                if const_ref in line:
                    # Replace $CONST with #value (add # prefix)
                    line = line.replace(const_ref, f"{self.number_prefix}{const_value}")
            
            resolved.append(line)
        
        return resolved
    
    def resolve_labels(self, lines: List[str], labels: Dict[str, int]) -> List[str]:
        """Replace label references with their addresses
        @label is replaced with #address (adds # prefix for immediate values)
        Case-insensitive matching
        """
        resolved = []
        
        for line in lines:
            # Replace all label references (case-insensitive)
            for label_name, label_addr in labels.items():
                # Use regex for true case-insensitive replacement
                # Escape special regex characters in label_name (like the dot in .Lelse0)
                pattern = re.escape(self.label_prefix + label_name)
                line = re.sub(pattern, f"{self.number_prefix}{label_addr}", line, flags=re.IGNORECASE)
            
            resolved.append(line)
        
        return resolved

    def parse_label_reference(self, token: str, labels: Dict[str, int]) -> Optional[LabelReference]:
        """Parse @label, @label.low, or @label.high references for LDI."""
        token = token.strip()
        if not token.startswith(self.label_prefix):
            return None

        raw_name = token[len(self.label_prefix):].strip()
        normalized = raw_name.upper()

        # Prefer an exact label match so labels containing dots still work.
        if normalized in labels:
            address = labels[normalized]
            return LabelReference(
                source_text=token,
                label_name=normalized,
                part="full",
                address=address,
                byte_value=address & 0xFF
            )

        suffix_map = {
            ".LOW": "low",
            ".LO": "low",
            ".HIGH": "high",
            ".HI": "high",
        }

        for suffix, part in suffix_map.items():
            if normalized.endswith(suffix):
                base_name = normalized[:-len(suffix)]
                if base_name in labels:
                    address = labels[base_name]
                    byte_value = address & 0xFF if part == "low" else (address >> 8) & 0xFF
                    return LabelReference(
                        source_text=token,
                        label_name=base_name,
                        part=part,
                        address=address,
                        byte_value=byte_value
                    )

        raise ValueError(f"Undefined label reference: {token}")

    def parse_source_line(self, line: str, labels: Dict[str, int], line_number: int) -> ParsedLine:
        """Parse a source line and keep label metadata when present."""
        instruction, args = self.parse_instruction(line)
        label_ref = None

        if instruction == "LDI" and len(args) == 1:
            label_ref = self.parse_label_reference(args[0], labels)

        return ParsedLine(
            line_number=line_number,
            raw_line=line,
            instruction=instruction,
            args=args,
            label_ref=label_ref
        )

    def collect_label_load_segments(self, parsed_lines: List[ParsedLine], start_index: int) -> List[LabelLoadSegment]:
        """Collect the contiguous RA-loading sequence for the same label."""
        start_line = parsed_lines[start_index]
        if not start_line.label_ref:
            return []

        label_name = start_line.label_ref.label_name
        segments = [LabelLoadSegment(start_line.label_ref)]
        current_segment = segments[0]

        for parsed in parsed_lines[start_index + 1:]:
            if parsed.instruction == "SMSBRA":
                current_segment.smsbra_used = True
                continue

            if parsed.instruction == "MOV" and len(parsed.args) == 2 and parsed.args[1].upper() == "RA":
                current_segment.mov_dests.add(parsed.args[0].upper())
                continue

            if parsed.instruction == "LDI" and parsed.label_ref and parsed.label_ref.label_name == label_name:
                current_segment = LabelLoadSegment(parsed.label_ref)
                segments.append(current_segment)
                continue

            break

        return segments

    def build_label_warnings(self, parsed_lines: List[ParsedLine]) -> List[str]:
        """Warn when label bytes need SMSBRA or an explicit high-byte load."""
        warnings = []

        for index, parsed in enumerate(parsed_lines):
            ref = parsed.label_ref
            if not ref:
                continue

            segments = self.collect_label_load_segments(parsed_lines, index)
            if not segments:
                continue

            current_segment = segments[0]
            byte_desc = "high byte" if ref.part == "high" else "low byte"

            if ref.byte_value > 0x7F and not current_segment.smsbra_used:
                warnings.append(
                    f"Line {parsed.line_number} ('{parsed.raw_line}'): "
                    f"{ref.source_text} resolves to {byte_desc} 0x{ref.byte_value:02X}; "
                    f"LDI only loads 7 bits, so add SMSBRA after this instruction."
                )

            if ref.part == "full" and ref.address > 0xFF:
                has_high_load = any(
                    segment.reference.part == "high" and "PRH" in segment.mov_dests
                    for segment in segments[1:]
                )
                if not has_high_load:
                    warnings.append(
                        f"Line {parsed.line_number} ('{parsed.raw_line}'): "
                        f"{ref.source_text} resolves to 16-bit address 0x{ref.address:04X}. "
                        f"This bare form only loads the low byte into RA; also load "
                        f"{self.label_prefix}{ref.label_name.lower()}.high and move it to PRH."
                    )

        return warnings
    
    def parse_instruction(self, line: str) -> Tuple[str, List[str]]:
        """Parse an instruction line into opcode and arguments
        Returns: (instruction_name, [arg1, arg2, ...])
        """
        # Split by whitespace and commas
        parts = line.replace(',', ' ').split()
        
        if not parts:
            raise ValueError("Empty instruction line")
        
        instruction = parts[0].upper()
        args = [arg.strip() for arg in parts[1:]]
        
        return instruction, args
    
    def encode_instruction(self, instruction: str, args: List[str], labels: Optional[Dict[str, int]] = None) -> str:
        """Encode a single instruction to binary"""
        
        # Special instructions (no arguments)
        if instruction in ["NOP", "HLT", "SMSBRA", "INX"]:
            if args:
                raise ValueError(f"{instruction} does not take arguments")
            return self.encoder.encode_special(instruction)
        
        # LDI (1 argument)
        elif instruction == "LDI":
            if len(args) != 1:
                raise ValueError(f"LDI requires 1 argument, got {len(args)}")
            label_ref = self.parse_label_reference(args[0], labels or {})
            if label_ref:
                immediate = label_ref.encoded_immediate
            else:
                immediate = self.to_decimal(args[0])
            return self.encoder.encode_ldi(immediate)
        
        # MOV (2 arguments)
        elif instruction == "MOV":
            if len(args) != 2:
                raise ValueError(f"MOV requires 2 arguments (dest, src), got {len(args)}")
            return self.encoder.encode_mov(args[0], args[1])
        
        # NOT (1 argument)
        elif instruction == "NOT":
            if len(args) != 1:
                raise ValueError(f"NOT requires 1 argument, got {len(args)}")
            return self.encoder.encode_not(args[0])
        
        # Arithmetic operations (1 argument)
        elif instruction in ["ADD", "SUB", "ADC", "SBC", "AND"]:
            if len(args) != 1:
                raise ValueError(f"{instruction} requires 1 argument, got {len(args)}")
            return self.encoder.encode_arithmetic(instruction, args[0])
        
        # XOR (1 argument)
        elif instruction == "XOR":
            if len(args) != 1:
                raise ValueError(f"XOR requires 1 argument, got {len(args)}")
            return self.encoder.encode_xor(args[0])
        
        # Immediate arithmetic (1 argument)
        elif instruction in ["ADDI", "SUBI"]:
            if len(args) != 1:
                raise ValueError(f"{instruction} requires 1 argument, got {len(args)}")
            immediate = self.to_decimal(args[0])
            return self.encoder.encode_immediate_arithmetic(instruction, immediate)
        
        # Jump instructions (no arguments)
        elif instruction in ["JMP", "JEQ", "JGT", "JLT", "JGE", "JLE", "JNE", "JC"]:
            if args:
                raise ValueError(f"{instruction} does not take arguments (use MOV PRL, #addr first)")
            return self.encoder.encode_jump(instruction)
        
        # CMP (1 argument)
        elif instruction == "CMP":
            if len(args) != 1:
                raise ValueError(f"CMP requires 1 argument, got {len(args)}")
            return self.encoder.encode_cmp(args[0])
        
        else:
            raise ValueError(f"Unknown instruction: {instruction}")
    
    def convert_to_machine_code(self, raw_lines: List[str]) -> Tuple[List[str], Dict[str, int], Dict[str, int]]:
        """Main conversion function: assembly source -> binary machine code
        Returns: (binary_lines, labels, constants)
        """
        self.last_warnings = []

        # Step 1: Clean lines
        lines = self.clean_lines(raw_lines)
        
        # Step 2: Extract constants
        constants, lines = self.extract_constants(lines)
        
        # Step 3: Extract labels
        labels, lines = self.extract_labels(lines)

        # Step 4: Resolve constants
        lines = self.resolve_constants(lines, constants)

        # Step 5: Parse instructions while preserving label intent
        parsed_lines = []
        for i, line in enumerate(lines):
            try:
                parsed_lines.append(self.parse_source_line(line, labels, i + 1))
            except Exception as e:
                raise ValueError(f"Error on line {i + 1} ('{line}'): {e}")

        self.last_warnings = self.build_label_warnings(parsed_lines)

        # Step 6: Encode instructions
        binary_lines = []
        for parsed in parsed_lines:
            try:
                binary = self.encode_instruction(parsed.instruction, parsed.args, labels=labels)
                binary_lines.append(f"{binary}\n")
            except Exception as e:
                raise ValueError(f"Error on line {parsed.line_number} ('{parsed.raw_line}'): {e}")
        
        return binary_lines, labels, constants
    
    def disassemble(self, binary_code: str) -> str:
        """Disassemble binary code to assembly mnemonics"""
        binary_code = binary_code.strip()
        
        if len(binary_code) != 8:
            raise ValueError(f"Invalid binary code length: {len(binary_code)}")
        
        # Check if it's LDI (IM7 = 1)
        if binary_code[0] == '1':
            immediate = int(binary_code[1:], 2)
            return f"LDI #{immediate}"
        
        # Parse standard instruction format
        im7 = binary_code[0]
        mv = binary_code[1]
        a1 = binary_code[2]
        a2 = binary_code[3]
        j = binary_code[4]
        s2 = binary_code[5]
        s1 = binary_code[6]
        s0 = binary_code[7]
        
        # Special instructions
        if binary_code == "00000000":
            return "NOP"
        elif binary_code == "00000001":
            return "HLT"
        elif binary_code == "00000010":
            return "SMSBRA"
        elif binary_code == "00000011":
            return "INX"
        
        # MOV instructions (MV = 1)
        if mv == '1':
            dest_bits = a1 + a2 + j
            src_bits = s2 + s1 + s0
            
            # Find destination and source
            dest = None
            src = None
            
            for name, bits in DESTINATIONS.items():
                if bits == dest_bits:
                    dest = name
                    break
            
            for name, bits in SOURCES.items():
                if bits == src_bits:
                    src = name
                    break
            
            if dest and src:
                return f"MOV {dest}, {src}"
            else:
                return f"MOV ?, ? (unknown encoding)"
        
        # Jump instructions (A1=1, A2J=000)
        if a1 == '1' and a2 + j + s2 == '000':
            condition_bits = s1 + s0
            conditions = ["JMP", "JEQ", "JGT", "JLT", "JGE", "JLE", "JNE", "JC"]
            condition_map = {f"{i:03b}"[1:]: conditions[i] for i in range(8)}
            return condition_map.get(condition_bits, f"J? (unknown)")
        
        # Immediate arithmetic (A1A2=11)
        if a1 + a2 == '11':
            immediate = int(s2 + s1 + s0, 2)
            if j == '0':
                return f"ADDI #{immediate}"
            else:
                return f"SUBI #{immediate}"
        
        # Other instructions
        return f"??? {binary_code}"
