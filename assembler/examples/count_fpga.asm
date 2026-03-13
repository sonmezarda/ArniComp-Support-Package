LDI #0
MOV RD, RA
mov prh, ra

ldi @add1
mov prl, ra

ldi #63

add1:
    ADDI #1
    mov rd, acc
    CMP ra
    JNE

HLT
HLT
  