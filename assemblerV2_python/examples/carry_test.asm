const SS_HIGH 0x10
const SS_LOW 0x00

ldi $SS_LOW
mov marl, ra
ldi $SS_HIGH
mov marh, ra

ldi #0b1111111
mov rd, ra
add ra

ldi #1
add ra
add ra



HLT