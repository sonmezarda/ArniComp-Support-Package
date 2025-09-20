ldi @read
mov prl, ra

ldi #0x20
mov marh, ra
ldi #0x00
mov marl, ra

read:
    mov ra, mh
    mov ml, ra
    jmp

hlt
