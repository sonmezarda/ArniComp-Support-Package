while_start_1:
ldi #10
mov rd, ra
ldi #0
mov marl, ra
cmp m
ldi @while_end_1
mov prl, ra
jge
mov rd, m
ldi #1
add ra
mov marl, acc
mov m, rd
ldi #0
mov marl, ra
mov rd, m
addi #1
mov m, acc
ldi @while_start_1
mov prl, ra
jmp
while_end_1:
