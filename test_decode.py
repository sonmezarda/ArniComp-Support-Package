"""
Debug instruction decode
"""

import sys
sys.path.append('emulator')

from cpu import CPU

def test_decode():
    cpu = CPU()
    
    # Test STRL ACC instruction: 01010110
    instruction = 0b01010110
    
    print(f"Testing instruction: {instruction:08b}")
    print(f"IM7: {(instruction >> 7) & 1}")
    print(f"Opcode: {(instruction >> 3) & 0xF:04b} ({(instruction >> 3) & 0xF})")
    print(f"Argcode: {instruction & 0x7:03b} ({instruction & 0x7})")
    
    inst_name, args = cpu.decode_instruction(instruction)
    print(f"Decoded as: {inst_name} {args}")
    
    # Test manually with the algorithm
    print("\n=== Manual Decode Debug ===")
    opcode = (instruction >> 3) & 0xF
    argcode = instruction & 0x7
    
    for inst_name_check, inst_data in cpu.instructions.items():
        if inst_name_check == 'STRL':
            print(f"Checking {inst_name_check}: {inst_data}")
            if inst_data.get('opcode_type') == 'constant':
                expected_opcode = inst_data.get('opcode')
                print(f"  Expected opcode: {expected_opcode} = {int(expected_opcode, 2)}")
                print(f"  Actual opcode: {opcode}")
                if int(expected_opcode, 2) == opcode:
                    print(f"  Opcode match!")
                    if inst_data.get('argcode_type') == 'out_reg':
                        print(f"  Looking for argcode {argcode} in out_reg")
                        for reg_name, reg_code in cpu.argcode_types['out_reg'].items():
                            print(f"    {reg_name}: {reg_code} = {int(reg_code, 2)}")
                            if int(reg_code, 2) == argcode:
                                print(f"    MATCH! Should return: {inst_name_check} [{reg_name.upper()}]")
    
    # Check if STRL is in instructions
    print(f"\nSTRL in instructions: {'STRL' in cpu.instructions}")
    if 'STRL' in cpu.instructions:
        strl_config = cpu.instructions['STRL']
        print(f"STRL config: {strl_config}")
        print(f"Expected opcode: {strl_config.get('opcode')} = {int(strl_config.get('opcode'), 2)}")

if __name__ == "__main__":
    test_decode()
