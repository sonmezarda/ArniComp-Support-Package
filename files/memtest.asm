const a1 = 0
const a2 = 1

ldi $a1
mov marl, ra

ldi #0b1010101
mov rd, ra
strl rd

ldi $a2
mov marl, ra

ldi #0b1111111
strl ra

ldi $a1
mov marl, ra

ldrl ra

ldi $a2
mov marl, ra

ldrl ra
