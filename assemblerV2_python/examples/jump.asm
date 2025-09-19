
ldi #0x00
mov prh, ra
mov rd, ra
add ra

ldi @label1
mov prl, ra

label1:
    ldi #0x01
    mov rd, ra
    add acc
    jmp 

hlt