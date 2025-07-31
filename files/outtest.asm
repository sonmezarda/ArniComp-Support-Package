ldi @lbl
mov prl, ra

ldi #0
mov rd, ra

lbl:
    addi #1 ; acc = rd + 1
    out acc
    mov rd, acc ; update rd with acc
    jmp