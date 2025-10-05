equ A 0x11
equ B 0x55

ldi $A
mov rd, ACC
ldi $B
add RA

mov RB, ACC
hlt
