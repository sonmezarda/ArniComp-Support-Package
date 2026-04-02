; Jump regression using final ISA encodings

    LDI @jump_target
    MOV PRL, RA
    CLR RA
    MOV PRH, RA
    JMP
    NOP

jump_target:
    LDI #0x11
    MOV RD, RA
    CMP RA

    LDI @eq_target
    MOV PRL, RA
    CLR RA
    MOV PRH, RA
    JEQ
    NOP

eq_target:
    LDI #0x22
    MOV RB, RA

    LDI @ne_target
    MOV PRL, RA
    CLR RA
    MOV PRH, RA
    JNE

    LDI #0x33
    MOV RD, RA
    LDI #0x11
    HLT

ne_target:
    LDI #0x44
    MOV RD, RA
    HLT
