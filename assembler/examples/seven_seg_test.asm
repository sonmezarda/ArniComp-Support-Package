equ SS_H 0x10
equ SS_L 0x00

ldi $SS_H
mov marh, ra
ldi $SS_L
mov marl, ra

ldi #10
mov m, ra

hlt
