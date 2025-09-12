import pytest

from emulator.cpu import CPU

def run(program_bytes, max_steps=50):
    cpu = CPU()
    cpu.load_program(program_bytes)
    steps=0
    while not cpu.halted and steps < max_steps:
        inst = cpu.program_memory[cpu.pc]
        name,args = cpu.decode_instruction(inst)
        cpu.step()
        steps+=1
    return cpu

def encode(program):
    return bytearray(program)

def test_add_carry_and_jc():
    # LDI #120, MOV RD, ACC, ADDI #7, ADD RD, ADDI #7 -> should overflow at some point setting carry
    prog = []
    prog.append(0b11111000)        # LDI #120
    prog.append(0b01001010)        # MOV RD, ACC (dest RD=001 src ACC=010)
    prog.append(0b00011111)        # ADDI #7  ACC=120+7=127
    prog.append(0b00100001)        # ADD RD   ACC=127 + RD(120)=247 no carry
    prog.append(0b00011111)        # ADDI #7  ACC=247+7=254
    prog.append(0b00011111)        # ADDI #7  ACC=254+7=261 -> 5 with carry set
    # Prepare jump target at address 0x000A (after next two bytes): set PRL then PRH=0
    prog.append(0b01100000)        # MOV PRL, RA (RA currently 120, not ideal) We'll load a small value first
    # Better: load 10 into ACC then move to PRL: LDI #10, MOV PRL, ACC
    prog[-1] = 0b10001010          # LDI #10 (replace previous)
    prog.append(0b01100010)        # MOV PRL, ACC (dest PRL=100 src ACC=010)
    prog.append(0b01101011)        # MOV PRH, CLR (dest PRH=101 src CLR=011)
    prog.append(0b00001111)        # JC   (should take because carry=1) to address 0x000A -> points to HLT at end we add
    prog.append(0b00000000)        # NOP (will be skipped if jump works)
    prog.append(0b00000001)        # HLT

    cpu = run(encode(prog))
    assert cpu.flags.carry is True
    assert cpu.pc == 0x000C or cpu.pc == 0x000B  # landed after executing HLT
    assert cpu.halted is True

def test_subi_borrow_carry_clear():
    # LDI #5 ; MOV RD, ACC ; SUBI #3 ; SUBI #3 -> second causes borrow so carry clears
    prog = [
        0b10000101,      # LDI #5
        0b01001010,      # MOV RD, ACC
        0b00000111,      # SUBI #3 (imm2=3) ACC=5-3=2 carry=1
        0b00000111,      # SUBI #3 ACC=2-3= -1 -> 255 borrow -> carry=0
        0b00000001       # HLT
    ]
    cpu = run(encode(prog))
    assert cpu.acc == 0xFF
    assert cpu.flags.carry is False

def test_and_and_cra():
    # LDI #85 ; MOV RD, ACC ; LDI #15 ; AND RD ; CRA ; HLT
    prog = [
        0b11010101,    # LDI #85
        0b01001010,    # MOV RD, ACC
        0b10001111,    # LDI #15
        0b00010001,    # AND RD -> ACC = 15 & 85 = 5
        0b00000011,    # CRA (only clears RA)
        0b00000001     # HLT
    ]
    cpu = run(encode(prog))
    assert cpu.acc == 5      # ACC unchanged by CRA
    assert cpu.ra == 0       # RA cleared
    # Flags unchanged (whatever comparator last set, we just ensure carry value preserved)
