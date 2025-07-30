"""
Test script to assemble and run programs in emulator
"""

import sys
import os
sys.path.append('modules')

from modules.AssemblyHelper import AssemblyHelper

def assemble_file(input_file, output_file):
    """Assemble a file to binary"""
    assembly_helper = AssemblyHelper(
        comment_char=';', 
        label_char=':', 
        constant_keyword="const", 
        number_prefix='#',
        constant_prefix='$',
        label_prefix='@'
    )
    
    # Read file
    with open(input_file, 'r') as f:
        raw_lines = f.readlines()
    
    # Process assembly
    clines = assembly_helper.upper_lines(raw_lines)
    clines = assembly_helper.remove_whitespaces_lines(raw_lines)
    print(f"Cleaned lines: {clines}")
    
    constants = assembly_helper.get_constants(clines)
    print(f"Constants found: {constants}")
    clines = assembly_helper.remove_constants(clines)
    
    labels = assembly_helper.get_labels(clines)
    clines = assembly_helper.remove_labels(clines)
    print(f"Labels found: {labels}")
    
    clines = assembly_helper.change_labels(clines, labels)
    clines = assembly_helper.change_constants(clines, constants)
    
    print(f"Final lines: {clines}")
    
    blines = assembly_helper.convert_to_binary_lines(clines)
    print(f"Binary lines: {blines}")
    
    # Write binary file
    with open(output_file, 'w') as f:
        for line in blines:
            f.write(f"{line}\n")
    
    print(f"Assembly complete: {output_file}")

def binary_to_bin(input_file, output_file):
    """Convert text binary to actual binary file"""
    program = bytearray(65536)
    
    with open(input_file, "r") as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            line = line.strip()
            if line:
                program[i] = int(line, 2)
    
    with open(output_file, "wb") as f:
        f.write(program)
    
    print(f"Binary file created: {output_file}")

if __name__ == "__main__":
    # Test with memtest2.asm
    input_file = "files/memtest2.asm"
    binary_text = "files/memtest2.binary"
    binary_file = "files/memtest2.bin"
    
    try:
        assemble_file(input_file, binary_text)
        binary_to_bin(binary_text, binary_file)
        print(f"\nReady to test with emulator:")
        print(f"python emulator/main.py {binary_file}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
