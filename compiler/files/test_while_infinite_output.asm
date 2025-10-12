while_start_1:
ldi #0
mov marl, ra
mov rd, m
addi #1
mov m, acc
mov rd, m
ldi #16
mov marh, ra
mov m, rd
ldi @while_start_1
mov prl, ra
jmp
