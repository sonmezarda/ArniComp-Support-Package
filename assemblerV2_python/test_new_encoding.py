import os, sys
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(BASE_DIR)
if PARENT not in sys.path:
    sys.path.insert(0, PARENT)
from assemblerV2_python.modules.AssemblyHelper import AssemblyHelper

def main():
    h = AssemblyHelper(';',':','const','#','@','&')
    lines = [
        'LDI #5',
        'MOV RA, RD',
        'MOV MARH, CLR',
        'ADD RD',
        'ADC ACC',
        'SBC ACC',  # expecting arithmetic code path
        'AND ML',
        'ADDI #3',
        'SUBI #2',
        'JMP',
        'JEQ',
        'JGT',
        'CRA',
        'HLT',
        'NOP'
    ]
    for l in lines:
        b = h.covert_to_binary(l)
        print(f'{l:14} -> {b} ({int(b,2):02X})')
    print('\nDisassembly:')
    for l in lines:
        b = h.covert_to_binary(l)
        print(h.disassemble_instruction(int(b,2)))

if __name__ == '__main__':
    main()
