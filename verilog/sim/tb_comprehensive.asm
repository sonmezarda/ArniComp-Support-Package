; Broad ISA smoke test with predictable final architectural state

    CLR RA
    MOV MARL, RA
    MOV MARH, RA

    LDI #0x05
    MOV RB, RA
    MOV M, RB
    MOV RA, M

    INC #1
    INC #1
    INC #1

    LDI @after_jump
    MOV PRL, RA
    CLR RA
    MOV PRH, RA
    JMP
    LDI #0x01

after_jump:
    LDI #0x32
    MOV RD, RA
    ADD RB
    SUBI #1
    XOR RB
    AND RA
    NOT RB
    CMP RA

    LDI #0x30
    MOV PRL, RA
    CLR RA
    MOV PRH, RA

    LDI #0x14
    SUB RA
    LDI #0x80
    HLT
