while_start_1:
    ldi #0
    mov marl, ra
    ldi #32
    mov marh, ra ; mar = 0x2000 (BUTTON)

    mov rd, m ; rd = BUTTON

    ldi #0
    mov marh, ra ; mar = 0x0000 (button)

    mov m, rd
    mov rd, m
    ldi #1
    and ra
    inx
    mov m, acc
    ldi #1
    mov rd, ra
    inx
    cmp m

    ldi @if_1
    mov prl, ra
    jne

    ldi #9
    mov rd, ra
    ldi #0
    mov marl, ra
    ldi #16
    mov marh, ra
    mov m, rd

    ldi @else_1
    mov prl, ra
    jmp

    if_1:
        ldi #2
        mov rd, ra
        mov m, rd
    else_1:
        ldi @while_start_1
        mov prl, ra
        jmp
