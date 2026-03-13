equ LEDADDR_H #0x01
equ LEDADDR_L #0x00

LDI #0
MOV RD, RA
mov prh, ra

ldi $LEDADDR_H
mov marh, ra

ldi $LEDADDR_L
mov marl, ra

ldi @add1
mov prl, ra

ldi #63

add1:
    ADDI #1
    mov rd, acc
    mov m, acc
    CMP ra
    JNE

HLT
HLT
  