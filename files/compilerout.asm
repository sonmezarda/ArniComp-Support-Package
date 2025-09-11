ldi #0
mov marl, ra
ldi #5
strl ra
while_start_1:
    out ra
    ldi @while_start_1
    mov prl, ra
jmp