#!/usr/bin/env python3
"""
Generate comprehensive test program for ArniComp
Tests all instruction categories and produces expected values
"""

# Instruction encodings
def ldi(imm):
    """LDI imm -> RA = imm (7-bit)"""
    return 0x80 | (imm & 0x7F)

def mov(dst, src):
    """MOV dst, src
    dst: RA=0, RD=1, RB=2, MARL=3, MARH=4, PRL=5, PRH=6, M=7
    src: RA=0, RD=1, RB=2, ACC=3, PCL=4, PCH=5, M=7
    """
    return 0x40 | ((src & 7) << 3) | (dst & 7)

def add_src(src):
    """ADD src -> ACC = RD + src"""
    return 0x08 | (src & 7)

def sub_src(src):
    """SUB src -> ACC = RD - src"""
    return 0x10 | (src & 7)

def adc_src(src):
    """ADC src -> ACC = RD + src + C"""
    return 0x18 | (src & 7)

def sbc_src(src):
    """SBC src -> ACC = RD - src - !C"""
    return 0x20 | (src & 7)

def and_src(src):
    """AND src -> ACC = RD & src"""
    return 0x28 | (src & 7)

def addi(imm):
    """ADDI imm -> ACC = RD + imm3"""
    return 0x30 | (imm & 7)

def subi(imm):
    """SUBI imm -> ACC = RD - imm3"""
    return 0x38 | (imm & 7)

def jmp(cond):
    """JMP cond: 0=JMP, 1=JEQ, 2=JGT, 3=JLT, 4=JGE, 5=JLE, 6=JNE, 7=JC"""
    return 0x60 | (cond & 7)

NOP = 0x00
HLT = 0x01
SMSBRA = 0x02
INX = 0x03
NOT_RB = 0x04
CMP_RA = 0x05
CMP_M = 0x06
CMP_ACC = 0x07

# XOR special encodings within ADD/SUB/ADC/SBC/AND ranges
XOR_RA = 0x0C   # 00001 100
XOR_RB = 0x14   # 00010 100  
XOR_ACC = 0x1A  # 00011 010
XOR_M = 0x24    # 00100 100
XOR_RD = 0x2C   # 00101 100

# NOT special encodings within MOV range
NOT_RA = 0x40   # 01 000 000
NOT_RD = 0x49   # 01 001 001
NOT_ACC = 0x52  # 01 010 010
NOT_M = 0x7F    # 01 111 111

# Register codes
RA, RD, RB, ACC = 0, 1, 2, 3
MARL, MARH, PRL, PRH, M = 3, 4, 5, 6, 7

# Jump conditions
JMP_ALWAYS, JEQ, JGT, JLT, JGE, JLE, JNE, JC = range(8)

# Build test program
program = []
expected = {
    'RA': 0, 'RD': 0, 'RB': 0, 'ACC': 0,
    'MARL': 0, 'MARH': 0, 'PRL': 0, 'PRH': 0
}

def emit(opcode, comment=""):
    program.append((opcode, comment))

# ========== Test 1: LDI ==========
emit(ldi(0x14), "LDI 20 -> RA=20")
expected['RA'] = 0x14

# ========== Test 2: MOV ==========
emit(mov(RD, RA), "MOV RD,RA -> RD=20")
expected['RD'] = 0x14

emit(ldi(0x05), "LDI 5 -> RA=5")
expected['RA'] = 0x05

emit(mov(RB, RA), "MOV RB,RA -> RB=5")
expected['RB'] = 0x05

# ========== Test 3: ADD ==========
# ACC = RD + RA = 20 + 5 = 25
emit(add_src(RA), "ADD RA -> ACC=RD+RA=20+5=25")
expected['ACC'] = 0x19

# ========== Test 4: ADDI ==========
emit(mov(RA, ACC), "MOV RA,ACC -> RA=25")
expected['RA'] = 0x19
emit(mov(RD, RA), "MOV RD,RA -> RD=25")
expected['RD'] = 0x19
# ACC = RD + 3 = 25 + 3 = 28
emit(addi(3), "ADDI 3 -> ACC=RD+3=25+3=28")
expected['ACC'] = 0x1C

# ========== Test 5: SUB ==========
emit(ldi(30), "LDI 30 -> RA=30")
expected['RA'] = 30
emit(mov(RD, RA), "MOV RD,RA -> RD=30")
expected['RD'] = 30
emit(ldi(10), "LDI 10 -> RA=10")
expected['RA'] = 10
# ACC = RD - RA = 30 - 10 = 20
emit(sub_src(RA), "SUB RA -> ACC=RD-RA=30-10=20")
expected['ACC'] = 20

# ========== Test 6: SUBI ==========
# ACC = RD - 5 = 30 - 5 = 25
emit(subi(5), "SUBI 5 -> ACC=RD-5=30-5=25")
expected['ACC'] = 25

# ========== Test 7: AND ==========
emit(ldi(0x0F), "LDI 0x0F -> RA=15")
expected['RA'] = 0x0F
emit(mov(RD, RA), "MOV RD,RA -> RD=15")
expected['RD'] = 0x0F
emit(ldi(0x55), "LDI 0x55 -> RA=0x55")
expected['RA'] = 0x55
# ACC = RD & RA = 0x0F & 0x55 = 0x05
emit(and_src(RA), "AND RA -> ACC=RD&RA=0x0F&0x55=0x05")
expected['ACC'] = 0x05

# ========== Test 8: XOR ==========
emit(ldi(0xFF), "LDI 0xFF -> RA=0xFF")
expected['RA'] = 0x7F  # Only 7 bits!
emit(mov(RD, RA), "MOV RD,RA -> RD=0x7F")
expected['RD'] = 0x7F
emit(ldi(0x0F), "LDI 0x0F -> RA=0x0F")
expected['RA'] = 0x0F
# ACC = RA XOR RD = 0x0F ^ 0x7F = 0x70
emit(XOR_RA, "XOR RA -> ACC=RA^RD=0x0F^0x7F=0x70")
expected['ACC'] = 0x70

# ========== Test 9: NOT ==========
emit(ldi(0x55), "LDI 0x55 -> RA=0x55")
expected['RA'] = 0x55
# ACC = ~RA = ~0x55 = 0xAA
emit(NOT_RA, "NOT RA -> ACC=~RA=0xAA")
expected['ACC'] = 0xAA

# ========== Test 10: INX ==========
emit(INX, "INX -> MARL=1")
expected['MARL'] = 1
emit(INX, "INX -> MARL=2")
expected['MARL'] = 2
emit(INX, "INX -> MARL=3")
expected['MARL'] = 3

# ========== Test 11: Jump setup (PRL/PRH) ==========
emit(ldi(0x30), "LDI 0x30 -> RA=0x30")
expected['RA'] = 0x30
emit(mov(PRL, RA), "MOV PRL,RA -> PRL=0x30")
expected['PRL'] = 0x30
emit(ldi(0x00), "LDI 0 -> RA=0")
expected['RA'] = 0
emit(mov(PRH, RA), "MOV PRH,RA -> PRH=0")
expected['PRH'] = 0

# ========== Test 12: SUB for final ACC and SMSBRA ==========
emit(ldi(50), "LDI 50 -> RA=50")
expected['RA'] = 50
emit(mov(RD, RA), "MOV RD,RA -> RD=50")
expected['RD'] = 50
emit(ldi(20), "LDI 20 -> RA=20")
expected['RA'] = 20
# ACC = RD - RA = 50 - 20 = 30
emit(sub_src(RA), "SUB RA -> ACC=RD-RA=50-20=30")
expected['ACC'] = 30

emit(ldi(0), "LDI 0 -> RA=0")
expected['RA'] = 0
emit(SMSBRA, "SMSBRA -> RA[7]=1 -> RA=0x80")
expected['RA'] = 0x80

emit(HLT, "HLT")

# Print program
print("// ArniComp Comprehensive Test Program")
print("// Auto-generated - Tests: LDI, MOV, ADD, SUB, ADDI, SUBI, AND, XOR, NOT, INX, SMSBRA")
print("@0")
for opcode, comment in program:
    print(f"{opcode:02X}")

print()
print("// Expected final state:")
for reg, val in expected.items():
    print(f"// {reg} = 0x{val:02X}")
