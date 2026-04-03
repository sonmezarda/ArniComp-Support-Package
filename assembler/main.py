#!/usr/bin/env python3
"""
ArniComp Assembler CLI
A command-line interface for assembling, disassembling, and managing binary files
for the ArniComp custom ISA architecture.

Usage:
    python main.py assemble <input.asm> [output.txt] [--listing output.lst] [--listing-mode hex|asm|both]
    python main.py disassemble <input.txt> [output.asm]
    python main.py createbin <input.txt> [output.bin]
    python main.py createihex <input.asm> [output.hex]
    python main.py createsvhex <input.asm> [output.mem] [--listing output.lst] [--listing-mode hex|asm|both]
    python main.py load <binary.bin>
    python main.py help
"""

import sys
import os
from typing import Optional

from modules.AssemblyHelper import AssemblyHelper


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
    
    def assemble(
        self,
        input_file: str,
        output_file: Optional[str] = None,
        listing_file: Optional[str] = None,
        listing_mode: str = "hex",
    ) -> None:
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
            binary_lines, labels, constants = self.helper.convert_to_machine_code(raw_lines, source_name=input_file)
            warnings = self.helper.last_warnings
            
            # Display info
            print(f"Assembly successful!")
            print(f"  Input: {input_file}")
            print(f"  Output: {output_file}")
            print(f"  Instructions: {len(binary_lines)}")
            print(f"  Labels: {len(labels)}")
            print(f"  Constants: {len(constants)}")
            print(f"  Warnings: {len(warnings)}")
            
            if labels:
                print("\n  Defined labels:")
                for label, addr in sorted(labels.items(), key=lambda x: x[1]):
                    print(f"    {label:20s} -> 0x{addr:04X} (line {addr})")
            
            if constants:
                print("\n  Defined constants:")
                for const, value in sorted(constants.items()):
                    print(f"    {const:20s} = 0x{value:02X} ({value})")

            if warnings:
                print("\n  Warnings:")
                for warning in warnings:
                    print(f"    {warning}")
            
            # Write output
            with open(output_file, 'w') as f:
                f.writelines(binary_lines)

            if listing_file:
                with open(listing_file, 'w', encoding='utf-8') as f:
                    f.writelines(self.helper.format_listing(listing_mode))
             
            print(f"\nBinary machine code written to: {output_file}")
            if listing_file:
                print(f"Listing written to: {listing_file}")
            
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
        from modules.HexConverter import save_intelHexFile
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
            binary_lines, labels, constants = self.helper.convert_to_machine_code(raw_lines, source_name=input_file)
            warnings = self.helper.last_warnings
            
            # Save as Intel HEX format
            save_intelHexFile(output_file, binary_lines, line_type='bin')
            
            print(f"Intel HEX file created successfully!")
            print(f"  Input: {input_file}")
            print(f"  Output: {output_file}")
            print(f"  Instructions: {len(binary_lines)}")
            print(f"  Format: Intel HEX (for Digital circuit simulator)")
            print(f"  Warnings: {len(warnings)}")
            
            if labels:
                print(f"  Labels: {len(labels)}")
            if constants:
                print(f"  Constants: {len(constants)}")
            if warnings:
                print("\n  Warnings:")
                for warning in warnings:
                    print(f"    {warning}")
            
        except Exception as e:
            print(f"Error creating Intel HEX file: {e}")
            sys.exit(1)

    def create_svhex(
        self,
        input_file: str,
        output_file: Optional[str] = None,
        listing_file: Optional[str] = None,
        listing_mode: str = "hex",
    ) -> None:
        """Convert assembly file to HEX format for SystemVerilog Program Mem"""
        # Determine output file
        if output_file is None:
            base_name = os.path.splitext(input_file)[0]
            output_file = f"{base_name}.mem"
        
        # Read input file
        try:
            with open(input_file, 'r') as f:
                raw_lines = f.readlines()
        except FileNotFoundError:
            print(f"Error: Input file '{input_file}' not found")
            sys.exit(1)
        
        # Assemble and convert to Intel HEX
        try:
            binary_lines, labels, constants = self.helper.convert_to_machine_code(raw_lines, source_name=input_file)
            warnings = self.helper.last_warnings
            
            with open(output_file, 'w') as f:
                f.write("@0\n")
                for binline in binary_lines:
                    hexLine = hex(int(binline, 2) &0xFF)[2:]
                    f.write(f"{hexLine:>02}\n")

            if listing_file:
                with open(listing_file, 'w', encoding='utf-8') as f:
                    f.writelines(self.helper.format_listing(listing_mode))

             
            print(f"HEX file created successfully!")
            print(f"  Input: {input_file}")
            print(f"  Output: {output_file}")
            print(f"  Instructions: {len(binary_lines)}")
            print(f"  Format: HEX (for SystemVerilog)")
            print(f"  Warnings: {len(warnings)}")
            
            if labels:
                print(f"  Labels: {len(labels)}")
            if constants:
                print(f"  Constants: {len(constants)}")
            if warnings:
                print("\n  Warnings:")
                for warning in warnings:
                    print(f"    {warning}")
            if listing_file:
                print(f"  Listing: {listing_file}")
             
        except Exception as e:
            print(f"Error creating SystemVerilog HEX file: {e}")
            sys.exit(1)
    
    def load_to_eeprom(self, bin_file: str) -> None:
        """Load a binary file to EEPROM"""
        from modules.EepromLoader import EepromLoader
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
        from modules.EepromLoader import EepromLoader
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
        from modules.EepromLoader import EepromLoader
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
    assemble <input.asm> [output.txt] [--listing output.lst] [--listing-mode hex|asm|both]
        Assemble assembly code to binary text format
        Example: python main.py assemble program.asm program.txt --listing program.lst --listing-mode both

    disassemble <input.txt> [output.asm]
        Disassemble binary text format back to assembly
        Example: python main.py disassemble program.txt program_dis.asm

    createbin <input.txt> [output.bin]
        Convert binary text format to .bin file
        Example: python main.py createbin program.txt program.bin

    createihex <input.asm> [output.hex]
        Assemble and convert to Intel HEX format (for Digital circuit simulator)
        Example: python main.py createihex program.asm program.hex

    createsvhex <input.asm> [output.mem] [--listing output.lst] [--listing-mode hex|asm|both]
        Assemble and convert to SystemVerilog HEX format
        Example: python main.py createsvhex program.asm program.mem --listing program.lst --listing-mode asm

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
    .include "file.asm"         ; Textual include
    .import "lib.asm" fn1, fn2  ; Import selected functions to program end
    .export NAME                ; Library export marker
    .func / .endfunc            ; Library function block
    
    LDL RA|RD, value            ; Load low 5 bits (0-31 or [4:0] slice)
    LDH RA|RD, value            ; Load high 3 bits (0-7 or [7:5] slice)
    LDI [RA|RD,] value          ; Pseudo over LDL/LDH, defaults to RA
    MOV dest, src               ; Move source to destination
    CLR dest                    ; Pseudo for MOV dest, ZERO
    ADD src                     ; ACC <- RD + src
    ADC src                     ; ACC <- RD + src + CF
    SUB src                     ; ACC <- RD - src
    SBC src                     ; ACC <- RD - src - CF
    AND src                     ; ACC <- RD and src
    XOR src                     ; ACC <- RD xor src
    NOT src                     ; ACC <- ~src
    ADDI #imm3                  ; Add immediate (0-7)
    SUBI #imm3                  ; Subtract immediate (0-7)
    CMP src                     ; Update flags only
    PUSH src                    ; Push source value
    POP dest                    ; Pop into destination
    JEQ, JNE, JCS, JCC, JMI, JVS, JLT, JMP, JGT
    JLE, JGE, JLEU             ; Assembler macros
    JZ, JNZ, JC, JNC, JN, JV,
    JGEU, JLTU, JLTS            ; Jump aliases
    JGTU target[:RA|:RD]        ; Unsigned greater-than target macro
    NOP, HLT, INC #1|#2, DEC #1|#2, JAL

REGISTERS:
    RA, RD, RB                  ; General purpose
    ACC                         ; Accumulator (source)
    PRL, PRH                    ; Program register
    MARL, MARH                  ; Memory address register
    LRL, LRH                    ; Link register bytes (source)
    M                           ; Memory[MARH:MARL]
    ZERO / 0 / #0               ; Zero-source alias for MOV

    NUMBER FORMATS:
        #10         Decimal
        #0x10       Hexadecimal
        #0b1010     Binary
        $CONST      Constant reference
        @label      Label reference
        value[hi:lo] Bit slice syntax

    LISTING OUTPUT:
        --listing file.lst
        Write a debug/listing file with:
        - final address
        - emitted bytes
        - source file and line
        - original source text
        --listing-mode hex|asm|both
        Choose hex summary view, expanded assembly view, or both

EXAMPLES:
    equ TARGET 0x1234
    
    start:
        LDI #10
        MOV RD, RA
        ADDI #1
        LDL RA, $TARGET[4:0]
        LDH RA, $TARGET[7:5]
        CLR RB
        JEQ done
        JGE retry :RD
        HLT

NOTES:
    - Bare jumps with no operand still jump to the address already in PRH:PRL.
    - Jump forms with a label or constant target are assembler pseudoinstructions:
      they load PRH:PRL first, then emit the jump.
    - Jump condition bits are ordered as:
      JEQ=000, JNE=001, JCS=010, JCC=011, JMI=100, JVS=101, JLT=110, JMP=111.
    - JLE expands to JEQ + JLT.
    - JGE expands to JEQ + JGT.
    - JLEU expands to JCC + JEQ.
    - JGTU is supported only with an explicit target operand.
    - ADD #imm and SUB #imm are not accepted; use ADDI / SUBI.
"""
        print(help_text)


def main():
    """Main entry point for the CLI"""
    def parse_assemble_args(arguments):
        if not arguments:
            raise ValueError("Input file required")

        input_file = arguments[0]
        output_file = None
        listing_file = None
        listing_mode = "hex"
        index = 1

        while index < len(arguments):
            token = arguments[index]
            if token == "--listing":
                if index + 1 >= len(arguments):
                    raise ValueError("--listing requires an output path")
                listing_file = arguments[index + 1]
                index += 2
                continue

            if token == "--listing-mode":
                if index + 1 >= len(arguments):
                    raise ValueError("--listing-mode requires one of: hex, asm, both")
                listing_mode = arguments[index + 1].lower()
                if listing_mode not in {"hex", "asm", "both"}:
                    raise ValueError("--listing-mode must be one of: hex, asm, both")
                index += 2
                continue

            if output_file is None:
                output_file = token
                index += 1
                continue

            raise ValueError(f"Unexpected assemble argument: {token}")

        return input_file, output_file, listing_file, listing_mode

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
            print("Usage: python main.py assemble <input.asm> [output.txt] [--listing output.lst] [--listing-mode hex|asm|both]")
            sys.exit(1)

        try:
            input_file, output_file, listing_file, listing_mode = parse_assemble_args(sys.argv[2:])
        except ValueError as e:
            print(f"Error: {e}")
            print("Usage: python main.py assemble <input.asm> [output.txt] [--listing output.lst] [--listing-mode hex|asm|both]")
            sys.exit(1)

        cli.assemble(input_file, output_file, listing_file, listing_mode)
    
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

    elif command == "createsvhex":
        if len(sys.argv) < 3:
            print("Error: Input file required")
            print("Usage: python main.py createsvhex <input.asm> [output.mem] [--listing output.lst] [--listing-mode hex|asm|both]")
            sys.exit(1)
        try:
            input_file, output_file, listing_file, listing_mode = parse_assemble_args(sys.argv[2:])
        except ValueError as e:
            print(f"Error: {e}")
            print("Usage: python main.py createsvhex <input.asm> [output.mem] [--listing output.lst] [--listing-mode hex|asm|both]")
            sys.exit(1)
        cli.create_svhex(input_file, output_file, listing_file, listing_mode)

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
