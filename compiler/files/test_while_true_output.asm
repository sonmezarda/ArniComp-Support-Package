ldi #1
mov marl, ra
while_start_1:
mov rd, m
addi #1
mov m, acc
ldi @while_start_1
mov prl, ra
jmp
