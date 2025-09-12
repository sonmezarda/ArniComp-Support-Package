import os, sys, pytest
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARENT = os.path.dirname(BASE)
if PARENT not in sys.path:
    sys.path.insert(0, PARENT)
from assemblerV2_python.modules.AssemblyHelper import AssemblyHelper

h = AssemblyHelper(';',':','const','#','@','&')

def asm(lines):
    return h.convert_to_machine_code(lines)[0][0:len(lines)]

@pytest.mark.parametrize("line,expected", [
    ("LDI #0",  "10000000"),
    ("LDI #127","11111111"),
])
def test_ldi_range(line, expected):
    out,_,_ = h.convert_to_machine_code([line])
    assert out[0].strip() == expected

@pytest.mark.parametrize("line,expected_prefix", [
    ("MOV RA, RD", "01"),
    ("MOV MH, ML", "01"),
])
def test_mov_prefix(line, expected_prefix):
    out,_,_ = h.convert_to_machine_code([line])
    assert out[0].startswith(expected_prefix)

@pytest.mark.parametrize("mnem,src,opbits", [
    ("ADD","RD","00100"),
    ("SUB","ML","00101"),
    ("ADC","ACC","00110"),
    ("SBC","MH","00111"),
])
def test_arith_encodings(mnem, src, opbits):
    out,_,_ = h.convert_to_machine_code([f"{mnem} {src}"])
    b = out[0].strip()
    assert b.startswith(opbits[:5])  # basic pattern check

@pytest.mark.parametrize("cond,bits", [
    ("JMP","00001000"),
    ("JEQ","00001001"),
    ("JGT","00001010"),
    ("JLT","00001011"),
    ("JGE","00001100"),
    ("JLE","00001101"),
    ("JNE","00001110"),
    ("JC", "00001111"),
])
def test_jump_encodings(cond, bits):
    out,_,_ = h.convert_to_machine_code([cond])
    assert out[0].strip() == bits

@pytest.mark.parametrize("addi,expected", [
    ("ADDI #0","00011000"),
    ("ADDI #7","00011111"),
])
def test_addi(addi, expected):
    out,_,_ = h.convert_to_machine_code([addi])
    assert out[0].strip() == expected

@pytest.mark.parametrize("subi,expected", [
    ("SUBI #0","00000100"),
    ("SUBI #3","00000111"),
])
def test_subi(subi, expected):
    out,_,_ = h.convert_to_machine_code([subi])
    assert out[0].strip() == expected

@pytest.mark.parametrize("andl,expected_prefix", [
    ("AND RA","00010000"),
    ("AND MH","00010111"),
])
def test_and(andl, expected_prefix):
    out,_,_ = h.convert_to_machine_code([andl])
    assert out[0].strip() == expected_prefix

# Error cases
def test_ldi_out_of_range():
    with pytest.raises(ValueError):
        h.convert_to_machine_code(["LDI #128"])  # 7-bit limiti aşar

def test_addi_out_of_range():
    with pytest.raises(ValueError):
        h.convert_to_machine_code(["ADDI #8"])  # 3-bit limiti aşar

def test_subi_out_of_range():
    with pytest.raises(ValueError):
        h.convert_to_machine_code(["SUBI #4"])  # 2-bit limiti aşar

def test_mov_invalid_dest():
    # ACC destination listesinde yok, hata beklenir
    with pytest.raises(ValueError):
        h.convert_to_machine_code(["MOV ACC, RA"])  

# Constant & label integration

def test_constants_labels():
    src = [
        'const A = #5',
        'const B = #3',
        'LBL:',
        'LDI $A',
        'ADDI $B',
        'LDI @LBL',
        'HLT'
    ]
    out,labels,constants = h.convert_to_machine_code(src)
    codes = [l.strip() for l in out]
    assert constants['A'] == 5 and constants['B'] == 3
    assert labels['LBL'] == 0
    # Expect sequence: LDI #5, ADDI #3, LDI #0, HLT
    assert codes[0].startswith('1') and codes[1].startswith('00011') and codes[2] == '10000000' and codes[3] == '00000001'

if __name__ == '__main__':
    import pytest, sys
    sys.exit(pytest.main([__file__]))
