; CMP and SBC regression

    LDI #127
    MOV RD, RA
    ADDI #7
    MOV RA, ACC
    MOV RD, RA
    LDI #127
    ADD RA

    LDI #20
    MOV RD, RA
    LDI #5
    SBC RA
    MOV RB, ACC

    LDI #20
    MOV RD, RA
    LDI #5
    CMP RA
    HLT
