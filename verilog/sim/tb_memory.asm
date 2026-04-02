; Memory regression

    LDI #0x10
    MOV MARL, RA
    CLR RA
    MOV MARH, RA

    LDI #0x55
    MOV M, RA
    MOV RB, M

    INC #1

    LDI #0x55
    NOT RA
    MOV M, ACC
    MOV RD, M
    HLT
