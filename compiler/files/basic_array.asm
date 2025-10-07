while_start_1:
    ldi #10
    mov rd, ra
    ldi #0
    mov marl, ra
    sub ml
    ldi @while_end_1
    mov prl, ra
    jge
    ldrl rd
    ldi #1
    add ra
    mov marl, acc
    ldi #5
    strl ra
    ldi #1
    add ra
    ldi #0
    mov marl, ra
    mov m, acc
    ldi @while_start_1
    mov prl, ra
    jmp
while_end_1:
