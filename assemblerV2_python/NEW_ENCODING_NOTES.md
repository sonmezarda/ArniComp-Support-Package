# New Instruction Encoding (Sept 2025)

This assembler version implements the revised 8-bit instruction encoding based on leading zero count.

Patterns:
- 1xxxxxxx : LDI #imm7
- 01dddsrc : MOV dst, src
- 001ooosrc: Arithmetic (ADD/SUB/ADC/SBC)
- 00010src : AND src
- 00011iii : ADDI #imm3
- 00001ccc : Jumps (JMP/JEQ/JGT/JLT/JGE/JLE/JNE/JC)
- 000001ii : SUBI #imm2
- 00000011 : CRA
- 00000001 : HLT
- 00000000 / 00000010 : NOP

Destination codes (d d d): RA(000) RD(001) MARL(010) MARH(011) PRL(100) PRH(101) ML(110) MH(111)
Source codes (s s s): RA(000) RD(001) ACC(010) CLR(011) PCL(100) PCH(101) ML(110) MH(111)

Arithmetic op (o o): ADD(00) SUB(01) ADC(10) SBC(11)
Jump cond (c c c): JMP(000) JEQ(001) JGT(010) JLT(011) JGE(100) JLE(101) JNE(110) JC(111)

Assembler logic is now hardcoded; old config opcode tables removed.
