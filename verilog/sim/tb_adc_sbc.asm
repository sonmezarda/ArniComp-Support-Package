; ADC and SBC carry-flow regression

    LDI #127
    MOV RD, RA
    ADDI #7
    MOV RA, ACC
    MOV RD, RA
    LDI #127
    ADD RA
    MOV RB, ACC

    LDI #0
    MOV RD, RA
    LDI #5
    ADC RA
    MOV RA, ACC
    HLT
