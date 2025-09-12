import os, sys
BASE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(BASE)
if PARENT not in sys.path:
    sys.path.insert(0, PARENT)
from assemblerV2_python.modules.AssemblyHelper import AssemblyHelper

def disasm(path):
    h = AssemblyHelper(';',':','const','#','@','&')
    with open(path,'r') as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]
    print(f'-- {path} --')
    for i,l in enumerate(lines):
        val = int(l,2)
        print(f'{i:02d}: {l} -> {h.disassemble_instruction(val)}')

if __name__=='__main__':
    disasm(os.path.join(BASE,'examples','example1.binary'))
    disasm(os.path.join(BASE,'examples','example2.binary'))
    disasm(os.path.join(BASE,'examples','constants_labels.binary'))
