equ A 0x11
equ B 0x55

ldi $A
mov rd, ra
ldi $B
add ra

mov rb, acc

not rb
mov rb, acc
hlt
