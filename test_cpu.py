"""
Simple test of the emulator
"""

import sys
sys.path.append('emulator')

from cpu import CPU

def test_simple_program():
    cpu = CPU()
    
    # Load the simple test program
    cpu.load_program_from_file('files/simple_test.bin')
    
    print("=== Testing Simple Program ===")
    print("Program: ldi #5, mov ra acc, ldi #10, add ra, strl acc")
    print()
    
    # Enable debug mode
    cpu.debug_mode = True
    
    print("Initial state:")
    cpu.print_debug_info()
    
    print("\n--- Step 1: ldi #5 ---")
    cpu.step()
    cpu.print_debug_info()
    
    print("\n--- Step 2: mov ra, acc ---")
    cpu.step()
    cpu.print_debug_info()
    
    print("\n--- Step 3: ldi #10 ---")
    cpu.step()
    cpu.print_debug_info()
    
    print("\n--- Step 4: add ra ---")
    cpu.step()
    cpu.print_debug_info()
    
    print("\n--- Step 5: strl acc ---")
    # Debug the instruction before executing
    next_inst = cpu.memory[cpu.pc]
    inst_name_debug, args_debug = cpu.decode_instruction(next_inst)
    print(f"About to execute: {inst_name_debug} {args_debug}")
    
    cpu.step()
    cpu.print_debug_info()
    
    # Check memory at address 0
    print(f"\nFinal result in memory[0]: {cpu.memory[0]}")
    print("Expected: 15 (5 + 10)")

if __name__ == "__main__":
    test_simple_program()
