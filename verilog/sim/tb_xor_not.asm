; XOR and NOT regression

    LDI #0x7F
    MOV RD, RA
    LDI #0x0F
    XOR RA
    MOV RB, ACC

    LDI #0x55
    NOT RA
    MOV RA, ACC
    HLT
