equ CONST1 5
equ CONST2 10

start:
    LDI #1
    MOV RD, RA
    LDI #2
    MOV RB, RA
    MOV MARL, RA
    LDI #0
    MOV MARH, RA
    LDI $CONST1
    MOV M, RA
    MOV RA, M

    MOV RD, RA
    LDI $CONST2
    ADD RA
    SUB RA
    ADC RA
    SBC RA
    AND RA
    XOR RA
    ADDI #3
    SUBI #2

    NOT RA
    SMSBRA
    INX

    MOV RD, RA
    LDI $CONST1
    CMP RA

    LDI @jump_tests
    MOV PRL, RA
    JMP

jump_tests:
    LDI @after_jeq
    MOV PRL, RA
    JEQ

after_jeq:
    LDI @after_jne
    MOV PRL, RA
    JNE

after_jne:
    LDI @after_jgt
    MOV PRL, RA
    JGT

after_jgt:
    LDI @after_jlt
    MOV PRL, RA
    JLT

after_jlt:
    LDI @after_jge
    MOV PRL, RA
    JGE

after_jge:
    LDI @after_jle
    MOV PRL, RA
    JLE

after_jle:
    LDI #127
    SMSBRA
    MOV RD, RA
    LDI #1
    ADD RA
    LDI @after_jc
    MOV PRL, RA
    JC

after_jc:
    NOP
    HLT
