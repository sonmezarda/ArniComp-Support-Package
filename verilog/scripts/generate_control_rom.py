#!/usr/bin/env python3
"""
ArniComp Control ROM Generator

Generates the 24-bit control ROM for all 256 possible instruction opcodes.
Based on the instruction encoding from the assembler and control_pkg.sv structure.

Control Word Structure (24-bit, MSB to LSB):
  Bit 23: nc_1 (not connected)
  Bit 22: inc (increment MARL for INX)
  Bit 21-20: ops[1:0] (ALU operation select)
  Bit 19: sn (set negative - NOT operation)
  Bit 18: ce (count enable - PC increment)
  Bit 17: jmp (jump active)
  Bit 16: sc (set carry)

  Bit 15: nc_2 (not connected)
  Bit 14: we (destination register write enable)
  Bit 13: accw (ACC write enable)
  Bit 12-10: dsel[2:0] (destination select)
  Bit 9: sf (set flags)
  Bit 8: im3 (use 3-bit immediate from instruction)

  Bit 7: nc_3 (not connected)
  Bit 6: nc_4 (not connected)
  Bit 5: smsbra (set MSB of RA)
  Bit 4-2: ssel[2:0] (source select)
  Bit 1: oe (output enable)
  Bit 0: im7 (use 7-bit immediate from instruction)

Destination encoding (dsel):
  000: RA, 001: RD, 010: RB, 011: MARL, 100: MARH, 101: PRL, 110: PRH, 111: M

Source encoding (ssel):
  000: RA, 001: RD, 010: RB, 011: ACC, 100: PCL, 101: PCH, 110: unused, 111: M

ALU ops encoding:
  00: ADD, 01: SUB, 10: AND, 11: XOR (or pass-through)
"""

import os

# Control word bit positions
BIT_NC1 = 23
BIT_INC = 22
BIT_OPS1 = 21
BIT_OPS0 = 20
BIT_SN = 19
BIT_CE = 18
BIT_JMP = 17
BIT_SC = 16

BIT_NC2 = 15
BIT_WE = 14
BIT_ACCW = 13
BIT_DSEL2 = 12
BIT_DSEL1 = 11
BIT_DSEL0 = 10
BIT_SF = 9
BIT_IM3 = 8

BIT_NC3 = 7
BIT_NC4 = 6
BIT_SMSBRA = 5
BIT_SSEL2 = 4
BIT_SSEL1 = 3
BIT_SSEL0 = 2
BIT_OE = 1
BIT_IM7 = 0

# Destination codes
DEST_RA = 0b000
DEST_RD = 0b001
DEST_RB = 0b010
DEST_MARL = 0b011
DEST_MARH = 0b100
DEST_PRL = 0b101
DEST_PRH = 0b110
DEST_M = 0b111

# Source codes
SRC_RA = 0b000
SRC_RD = 0b001
SRC_RB = 0b010
SRC_ACC = 0b011
SRC_PCL = 0b100
SRC_PCH = 0b101
SRC_M = 0b111

# ALU operations (ops field)
# ops=00: ADD (sn=0) or SUB (sn=1)
# ops=01: AND
# ops=10: XOR
# ops=11: NOT (uses ~a)
ALU_ADD = 0b00  # ADD when sn=0
ALU_SUB = 0b00  # SUB when sn=1 (same ops, different sn)
ALU_AND = 0b01
ALU_XOR = 0b10
ALU_NOT = 0b11


def make_ctrl(inc=0, ops=0, sn=0, ce=1, jmp=0, sc=0,
              we=0, accw=0, dsel=0, sf=0, im3=0,
              smsbra=0, ssel=0, oe=0, im7=0):
    """Build a 24-bit control word from individual signals."""
    ctrl = 0
    ctrl |= (inc & 1) << BIT_INC
    ctrl |= (ops & 3) << BIT_OPS0
    ctrl |= (sn & 1) << BIT_SN
    ctrl |= (ce & 1) << BIT_CE
    ctrl |= (jmp & 1) << BIT_JMP
    ctrl |= (sc & 1) << BIT_SC
    ctrl |= (we & 1) << BIT_WE
    ctrl |= (accw & 1) << BIT_ACCW
    ctrl |= (dsel & 7) << BIT_DSEL0
    ctrl |= (sf & 1) << BIT_SF
    ctrl |= (im3 & 1) << BIT_IM3
    ctrl |= (smsbra & 1) << BIT_SMSBRA
    ctrl |= (ssel & 7) << BIT_SSEL0
    ctrl |= (oe & 1) << BIT_OE
    ctrl |= (im7 & 1) << BIT_IM7
    return ctrl


def generate_control_rom():
    """Generate control words for all 256 instruction opcodes."""
    rom = [0] * 256
    
    # Default: NOP (ce=1, everything else 0)
    nop_ctrl = make_ctrl(ce=1)
    for i in range(256):
        rom[i] = nop_ctrl
    
    # ========================================
    # Special Instructions (0x00-0x07)
    # ========================================
    
    # 0x00: NOP - no operation, just increment PC
    rom[0x00] = make_ctrl(ce=1)
    
    # 0x01: HLT - halt (ce=0, no PC increment)
    rom[0x01] = make_ctrl(ce=0)
    
    # 0x02: SMSBRA - set MSB of RA
    rom[0x02] = make_ctrl(ce=1, smsbra=1)
    
    # 0x03: INX - increment MARL
    rom[0x03] = make_ctrl(ce=1, inc=1)
    
    # 0x04: NOT RB - ACC = ~RB (via ALU with ops=11)
    rom[0x04] = make_ctrl(ce=1, ops=ALU_NOT, accw=1, ssel=SRC_RB)
    
    # 0x05: CMP RA - compare RA with RD, set flags
    rom[0x05] = make_ctrl(ce=1, sf=1, ssel=SRC_RA)
    
    # 0x06: CMP M - compare M with RD, set flags
    rom[0x06] = make_ctrl(ce=1, sf=1, ssel=SRC_M)
    
    # 0x07: CMP ACC - compare ACC with RD, set flags
    rom[0x07] = make_ctrl(ce=1, sf=1, ssel=SRC_ACC)
    
    # ========================================
    # ADD Instructions (0x08-0x0F): ACC = ACC + src
    # ========================================
    for src in range(8):
        opcode = 0x08 | src
        if src == 0b100:  # 0x0C: XOR RA (special case)
            rom[opcode] = make_ctrl(ce=1, ops=ALU_XOR, accw=1, sf=1, ssel=SRC_RA)
        else:
            rom[opcode] = make_ctrl(ce=1, ops=ALU_ADD, accw=1, sf=1, ssel=src)
    
    # ========================================
    # SUB Instructions (0x10-0x17): ACC = ACC - src
    # ========================================
    for src in range(8):
        opcode = 0x10 | src
        if src == 0b100:  # 0x14: XOR RB (special case)
            rom[opcode] = make_ctrl(ce=1, ops=ALU_XOR, accw=1, sf=1, ssel=SRC_RB)
        else:
            rom[opcode] = make_ctrl(ce=1, ops=ALU_SUB, sn=1, accw=1, sf=1, ssel=src)
    
    # ========================================
    # ADC Instructions (0x18-0x1F): ACC = ACC + src + carry
    # ========================================
    for src in range(8):
        opcode = 0x18 | src
        if src == 0b010:  # 0x1A: XOR ACC (special case)
            rom[opcode] = make_ctrl(ce=1, ops=ALU_XOR, accw=1, sf=1, ssel=SRC_ACC)
        else:
            rom[opcode] = make_ctrl(ce=1, ops=ALU_ADD, accw=1, sf=1, sc=1, ssel=src)
    
    # ========================================
    # SBC Instructions (0x20-0x27): ACC = ACC - src - carry
    # ========================================
    for src in range(8):
        opcode = 0x20 | src
        if src == 0b100:  # 0x24: XOR M (special case)
            rom[opcode] = make_ctrl(ce=1, ops=ALU_XOR, accw=1, sf=1, ssel=SRC_M)
        else:
            rom[opcode] = make_ctrl(ce=1, ops=ALU_SUB, sn=1, accw=1, sf=1, sc=1, ssel=src)
    
    # ========================================
    # AND Instructions (0x28-0x2F): ACC = ACC & src
    # ========================================
    for src in range(8):
        opcode = 0x28 | src
        if src == 0b100:  # 0x2C: XOR RD (special case)
            rom[opcode] = make_ctrl(ce=1, ops=ALU_XOR, accw=1, sf=1, ssel=SRC_RD)
        else:
            rom[opcode] = make_ctrl(ce=1, ops=ALU_AND, accw=1, sf=1, ssel=src)
    
    # ========================================
    # ADDI Instructions (0x30-0x37): ACC = ACC + imm3
    # ========================================
    for imm in range(8):
        opcode = 0x30 | imm
        rom[opcode] = make_ctrl(ce=1, ops=ALU_ADD, accw=1, sf=1, im3=1)
    
    # ========================================
    # SUBI Instructions (0x38-0x3F): ACC = ACC - imm3
    # ========================================
    for imm in range(8):
        opcode = 0x38 | imm
        rom[opcode] = make_ctrl(ce=1, ops=ALU_SUB, sn=1, accw=1, sf=1, im3=1)
    
    # ========================================
    # MOV Instructions (0x40-0x7F): MOV dst, src
    # Format: 01 sss ddd
    # ========================================
    for src in range(8):
        for dst in range(8):
            opcode = 0x40 | (src << 3) | dst
            
            # Check for NOT instructions (special MOV encodings)
            if opcode == 0b01000000:  # NOT RA: src=0, dst=0
                rom[opcode] = make_ctrl(ce=1, ops=ALU_NOT, accw=1, ssel=SRC_RA)
            elif opcode == 0b01001001:  # NOT RD: src=1, dst=1  
                rom[opcode] = make_ctrl(ce=1, ops=ALU_NOT, accw=1, ssel=SRC_RD)
            elif opcode == 0b01010010:  # NOT ACC: src=2, dst=2
                rom[opcode] = make_ctrl(ce=1, ops=ALU_NOT, accw=1, ssel=SRC_ACC)
            elif opcode == 0b01111111:  # NOT M: src=7, dst=7
                rom[opcode] = make_ctrl(ce=1, ops=ALU_NOT, accw=1, ssel=SRC_M)
            elif src == 0b110:  # 0x70-0x77: Reserved/unused
                rom[opcode] = make_ctrl(ce=1)  # NOP
            else:
                # Normal MOV instruction
                rom[opcode] = make_ctrl(ce=1, we=1, dsel=dst, ssel=src, oe=1)
    
    # ========================================
    # JMP Instructions (0x60-0x67): Conditional jumps
    # Format: 01100 ccc (overwrite MOV entries)
    # ========================================
    for cond in range(8):
        opcode = 0x60 | cond
        rom[opcode] = make_ctrl(ce=1, jmp=1)
    
    # ========================================
    # LDI Instructions (0x80-0xFF): Load 7-bit immediate to RA
    # Format: 1 iii iiii
    # ========================================
    for imm in range(128):
        opcode = 0x80 | imm
        rom[opcode] = make_ctrl(ce=1, we=1, dsel=DEST_RA, im7=1)
    
    return rom


def write_rom_file(rom, filename):
    """Write ROM contents to a hex file."""
    with open(filename, 'w') as f:
        f.write("// ArniComp Control ROM - Auto-generated\n")
        f.write("// 256 x 24-bit entries\n")
        f.write("@0\n")
        for i, ctrl in enumerate(rom):
            f.write(f"{ctrl:06X}\n")
    print(f"Written {len(rom)} entries to {filename}")


def print_instruction_debug(rom):
    """Print decoded control words for debugging."""
    test_opcodes = [
        (0x00, "NOP"),
        (0x01, "HLT"),
        (0x02, "SMSBRA"),
        (0x03, "INX"),
        (0x08, "ADD RA"),
        (0x10, "SUB RA"),
        (0x30, "ADDI 0"),
        (0x38, "SUBI 0"),
        (0x48, "MOV RA,RD"),
        (0x60, "JMP"),
        (0x80, "LDI 0"),
        (0x8A, "LDI 10"),
        (0xD5, "LDI 85"),
        (0xFF, "LDI 127"),
    ]
    
    print("\n=== Control Word Debug ===")
    for opcode, name in test_opcodes:
        ctrl = rom[opcode]
        print(f"0x{opcode:02X} {name:12} -> 0x{ctrl:06X}")
        print(f"    ce={bool(ctrl & (1<<BIT_CE)):d} jmp={bool(ctrl & (1<<BIT_JMP)):d} "
              f"we={bool(ctrl & (1<<BIT_WE)):d} accw={bool(ctrl & (1<<BIT_ACCW)):d} "
              f"im7={bool(ctrl & (1<<BIT_IM7)):d} im3={bool(ctrl & (1<<BIT_IM3)):d}")
        print(f"    dsel={((ctrl>>BIT_DSEL0)&7):03b} ssel={((ctrl>>BIT_SSEL0)&7):03b} "
              f"ops={((ctrl>>BIT_OPS0)&3):02b} sf={bool(ctrl & (1<<BIT_SF)):d}")
    print()


if __name__ == "__main__":
    rom = generate_control_rom()
    
    # Determine output path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    rom_dir = os.path.join(script_dir, "..", "rom")
    os.makedirs(rom_dir, exist_ok=True)
    
    output_file = os.path.join(rom_dir, "control_rom.mem")
    write_rom_file(rom, output_file)
    
    print_instruction_debug(rom)
    print(f"Control ROM generated: {output_file}")
