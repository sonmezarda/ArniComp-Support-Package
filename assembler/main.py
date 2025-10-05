#!/usr/bin/env python3
"""
ArniComp Assembler CLI
A command-line interface for assembling, disassembling, and managing binary files
for the ArniComp custom ISA architecture.

Usage:
    python main.py assemble <input.asm> [output.txt]
    python main.py disassemble <input.txt> [output.asm]
    python main.py createbin <input.txt> [output.bin]
    python main.py load <binary.bin>
    python main.py help
"""

import sys
import os
import argparse
from typing import Optional

from modules.AssemblyHelper import AssemblyHelper
from modules.EepromLoader import EepromLoader
from modules.HexConverter import save_intelHexFile


class AssemblerCLI:
    """Command-line interface for the assembler"""
    
    def __init__(self, comport: str = "/dev/ttyACM0"):
        self.helper = AssemblyHelper(
            comment_char=';',
            label_char=':',
            constant_keyword='equ',
            number_prefix='#',
            constant_prefix='$',
            label_prefix='@'
        )
        self.comport = comport
    
    def assemble(self, input_file: str, output_file: Optional[str] = None) -> None:
        """Assemble an assembly file to binary machine code"""
        # Determine output file
        if output_file is None:
            base_name = os.path.splitext(input_file)[0]
            output_file = f"{base_name}.bin"
        
        # Read input file
        try:
            with open(input_file, 'r') as f:
                raw_lines = f.readlines()
        except FileNotFoundError:
            print(f"Error: Input file '{input_file}' not found")
            sys.exit(1)
        
        # Assemble
        try:
            binary_lines, labels, constants = self.helper.convert_to_machine_code(raw_lines)
            
            # Display info
            print(f"Assembly successful!")
            print(f"  Input: {input_file}")
            print(f"  Output: {output_file}")
            print(f"  Instructions: {len(binary_lines)}")
            print(f"  Labels: {len(labels)}")
            print(f"  Constants: {len(constants)}")
            
            if labels:
                print("\n  Defined labels:")
                for label, addr in sorted(labels.items(), key=lambda x: x[1]):
                    print(f"    {label:20s} -> 0x{addr:04X} (line {addr})")
            
            if constants:
                print("\n  Defined constants:")
                for const, value in sorted(constants.items()):
                    print(f"    {const:20s} = 0x{value:02X} ({value})")
            
            # Write output
            with open(output_file, 'w') as f:
                f.writelines(binary_lines)
            
            print(f"\nBinary machine code written to: {output_file}")
            
        except Exception as e:
            print(f"Assembly error: {e}")
            sys.exit(1)
    
    def disassemble(self, input_file: str, output_file: Optional[str] = None) -> None:
        """Disassemble binary machine code to assembly mnemonics"""
        # Determine output file
        if output_file is None:
            base_name = os.path.splitext(input_file)[0]
            output_file = f"{base_name}.asm"
        
        # Read binary file
        try:
            with open(input_file, 'r') as f:
                binary_lines = f.readlines()
        except FileNotFoundError:
            print(f"Error: Input file '{input_file}' not found")
            sys.exit(1)
        
        # Disassemble
        try:
            assembly_lines = []
            for i, binary_line in enumerate(binary_lines):
                binary_line = binary_line.strip()
                if binary_line:
                    try:
                        asm = self.helper.disassemble(binary_line)
                        assembly_lines.append(f"{asm}\n")
                    except Exception as e:
                        assembly_lines.append(f"; ERROR: {e}\n")
            
            # Write output
            with open(output_file, 'w') as f:
                f.writelines(assembly_lines)
            
            print(f"Disassembly successful!")
            print(f"  Input: {input_file}")
            print(f"  Output: {output_file}")
            print(f"  Instructions: {len(assembly_lines)}")
            
        except Exception as e:
            print(f"Disassembly error: {e}")
            sys.exit(1)
    
    def create_bin(self, input_file: str, output_file: Optional[str] = None) -> None:
        """Convert text binary format to .bin file"""
        # Determine output file
        if output_file is None:
            base_name = os.path.splitext(input_file)[0]
            output_file = f"{base_name}.bin"
        
        # Create binary program
        program = bytearray(65536)  # 64KB address space
        
        try:
            with open(input_file, 'r') as f:
                lines = f.readlines()
                
            for i, line in enumerate(lines):
                line = line.strip()
                if line:
                    try:
                        program[i] = int(line, 2)
                    except ValueError:
                        print(f"Warning: Invalid binary format on line {i + 1}: {line}")
            
            # Write binary file
            with open(output_file, 'wb') as f:
                f.write(program)
            
            print(f"Binary file created successfully!")
            print(f"  Input: {input_file}")
            print(f"  Output: {output_file}")
            print(f"  Size: {len(program)} bytes")
            print(f"  Instructions loaded: {i + 1}")
            
        except FileNotFoundError:
            print(f"Error: Input file '{input_file}' not found")
            sys.exit(1)
        except Exception as e:
            print(f"Error creating binary file: {e}")
            sys.exit(1)
    
    def create_ihex(self, input_file: str, output_file: Optional[str] = None) -> None:
        """Convert assembly file to Intel HEX format for Digital circuit simulator"""
        # Determine output file
        if output_file is None:
            base_name = os.path.splitext(input_file)[0]
            output_file = f"{base_name}.hex"
        
        # Read input file
        try:
            with open(input_file, 'r') as f:
                raw_lines = f.readlines()
        except FileNotFoundError:
            print(f"Error: Input file '{input_file}' not found")
            sys.exit(1)
        
        # Assemble and convert to Intel HEX
        try:
            binary_lines, labels, constants = self.helper.convert_to_machine_code(raw_lines)
            
            # Save as Intel HEX format
            save_intelHexFile(output_file, binary_lines, line_type='bin')
            
            print(f"Intel HEX file created successfully!")
            print(f"  Input: {input_file}")
            print(f"  Output: {output_file}")
            print(f"  Instructions: {len(binary_lines)}")
            print(f"  Format: Intel HEX (for Digital circuit simulator)")
            
            if labels:
                print(f"  Labels: {len(labels)}")
            if constants:
                print(f"  Constants: {len(constants)}")
            
        except Exception as e:
            print(f"Error creating Intel HEX file: {e}")
            sys.exit(1)
    
    def load_to_eeprom(self, bin_file: str) -> None:
        """Load a binary file to EEPROM"""
        try:
            eeprom_loader = EepromLoader(self.comport)
            print(f"Loading {bin_file} to EEPROM via {self.comport}...")
            eeprom_loader.write(bin_file)
            print("EEPROM load completed successfully!")
        except FileNotFoundError:
            print(f"Error: Binary file '{bin_file}' not found")
            sys.exit(1)
        except Exception as e:
            print(f"Error loading to EEPROM: {e}")
            sys.exit(1)
    
    def assemble_and_load(self, asm_file: str) -> None:
        """Assemble and load directly to EEPROM (uses temporary files)"""
        tmp_txt = "_tmp_machine.txt"
        tmp_bin = "_tmp_program.bin"
        
        try:
            # Step 1: Assemble
            print("Step 1/3: Assembling...")
            self.assemble(asm_file, tmp_txt)
            
            # Step 2: Create binary
            print("\nStep 2/3: Creating binary file...")
            self.create_bin(tmp_txt, tmp_bin)
            
            # Step 3: Load to EEPROM
            print("\nStep 3/3: Loading to EEPROM...")
            self.load_to_eeprom(tmp_bin)
            
            print("\nComplete! Program assembled and loaded to EEPROM.")
            
        finally:
            # Clean up temporary files
            if os.path.exists(tmp_txt):
                os.remove(tmp_txt)
            if os.path.exists(tmp_bin):
                os.remove(tmp_bin)
    
    def verify_file(self, bin_file: str, bytes_to_check: int = 16) -> None:
        """Verify EEPROM contents against a binary file"""
        try:
            eeprom_loader = EepromLoader(self.comport)
            data = eeprom_loader.check_file(bin_file, bytes_to_check)
            print(f"First {bytes_to_check} bytes from EEPROM:")
            print(" ".join(f"{b:02X}" for b in data))
        except Exception as e:
            print(f"Error verifying file: {e}")
            sys.exit(1)
    
    def check_serial(self) -> None:
        """Check serial connection"""
        try:
            eeprom_loader = EepromLoader(self.comport)
            eeprom_loader.check_serial()
            print("Serial connection OK!")
        except Exception as e:
            print(f"Error checking serial: {e}")
            sys.exit(1)
    
    def display_help(self) -> None:
        """Display help information"""
        help_text = """
ArniComp Assembler - Command Line Interface

USAGE:
    python main.py <command> [arguments]

COMMANDS:
    assemble <input.asm> [output.txt]
        Assemble assembly code to binary text format
        Example: python main.py assemble program.asm program.txt

    disassemble <input.txt> [output.asm]
        Disassemble binary text format back to assembly
        Example: python main.py disassemble program.txt program_dis.asm

    createbin <input.txt> [output.bin]
        Convert binary text format to .bin file
        Example: python main.py createbin program.txt program.bin

    createihex <input.asm> [output.hex]
        Assemble and convert to Intel HEX format (for Digital circuit simulator)
        Example: python main.py createihex program.asm program.hex

    load <binary.bin>
        Load a binary file to EEPROM
        Example: python main.py load program.bin

    loadasm <input.asm>
        Assemble and load directly to EEPROM (all-in-one)
        Example: python main.py loadasm program.asm

    verify <binary.bin> [bytes]
        Verify EEPROM contents against binary file
        Example: python main.py verify program.bin 32

    checkserial
        Check serial connection to EEPROM loader
        Example: python main.py checkserial

    help
        Display this help message

ASSEMBLY SYNTAX:
    ; Comments start with semicolon
    equ CONSTANT_NAME value     ; Define constants
    label:                      ; Define labels
    
    LDI #immediate              ; Load immediate (0-127)
    MOV dest, src               ; Move data
    ADD src                     ; Add to RD, result in ACC
    SUB src                     ; Subtract from RD
    ADC src                     ; Add with carry
    SBC src                     ; Subtract with carry
    AND src                     ; Bitwise AND
    XOR src                     ; Bitwise XOR
    NOT src                     ; Bitwise NOT
    ADDI #imm3                  ; Add immediate (0-7)
    SUBI #imm3                  ; Subtract immediate (0-7)
    CMP src                     ; Compare (RA, M, ACC only)
    JMP, JEQ, JGT, JLT, JGE, JLE, JNE, JC
    NOP, HLT, SMSBRA, INX

REGISTERS:
    RA, RD, RB                  ; General purpose
    ACC                         ; Accumulator
    PCL, PCH                    ; Program counter
    PRL, PRH                    ; Program register
    MARL, MARH                  ; Memory address register
    M                           ; Memory[MARH:MARL]

NUMBER FORMATS:
    #10         Decimal
    #0x10       Hexadecimal
    #0b1010     Binary

EXAMPLES:
    equ COUNTER 0x00
    equ MAX 100
    
    start:
        LDI #0
        MOV RA, RA
        ADD RD
    loop:
        ADDI #1
        CMP #MAX
        JLT
        HLT
"""
        print(help_text)


def main():
    """Main entry point for the CLI"""
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Error: No command specified")
        print("Use 'python main.py help' for usage information")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    # Initialize CLI
    cli = AssemblerCLI()
    
    # Execute command
    if command == "help":
        cli.display_help()
    
    elif command == "assemble":
        if len(sys.argv) < 3:
            print("Error: Input file required")
            print("Usage: python main.py assemble <input.asm> [output.txt]")
            sys.exit(1)
        
        input_file = sys.argv[2]
        output_file = sys.argv[3] if len(sys.argv) >= 4 else None
        cli.assemble(input_file, output_file)
    
    elif command == "disassemble":
        if len(sys.argv) < 3:
            print("Error: Input file required")
            print("Usage: python main.py disassemble <input.txt> [output.asm]")
            sys.exit(1)
        
        input_file = sys.argv[2]
        output_file = sys.argv[3] if len(sys.argv) >= 4 else None
        cli.disassemble(input_file, output_file)
    
    elif command == "createbin":
        if len(sys.argv) < 3:
            print("Error: Input file required")
            print("Usage: python main.py createbin <input.txt> [output.bin]")
            sys.exit(1)
        
        input_file = sys.argv[2]
        output_file = sys.argv[3] if len(sys.argv) >= 4 else None
        cli.create_bin(input_file, output_file)
    
    elif command == "createihex":
        if len(sys.argv) < 3:
            print("Error: Input file required")
            print("Usage: python main.py createihex <input.asm> [output.hex]")
            sys.exit(1)
        
        input_file = sys.argv[2]
        output_file = sys.argv[3] if len(sys.argv) >= 4 else None
        cli.create_ihex(input_file, output_file)
    
    elif command == "load":
        if len(sys.argv) < 3:
            print("Error: Binary file required")
            print("Usage: python main.py load <binary.bin>")
            sys.exit(1)
        
        bin_file = sys.argv[2]
        cli.load_to_eeprom(bin_file)
    
    elif command == "loadasm":
        if len(sys.argv) < 3:
            print("Error: Assembly file required")
            print("Usage: python main.py loadasm <input.asm>")
            sys.exit(1)
        
        asm_file = sys.argv[2]
        cli.assemble_and_load(asm_file)
    
    elif command == "verify":
        if len(sys.argv) < 3:
            print("Error: Binary file required")
            print("Usage: python main.py verify <binary.bin> [bytes]")
            sys.exit(1)
        
        bin_file = sys.argv[2]
        bytes_to_check = int(sys.argv[3]) if len(sys.argv) >= 4 else 16
        cli.verify_file(bin_file, bytes_to_check)
    
    elif command == "checkserial":
        cli.check_serial()
    
    else:
        print(f"Error: Unknown command '{command}'")
        print("Use 'python main.py help' for usage information")
        sys.exit(1)


if __name__ == "__main__":
    main()
