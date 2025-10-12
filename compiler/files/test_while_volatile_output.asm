ldi #0
mov marl, ra
ldi #32
mov marh, ra
mov rd, m
mov m, rd
while_start_1:
ldi #10
mov rd, ra
cmp m
ldi @while_end_1
mov prl, ra
jge
inx
mov rd, m
addi #1
mov m, acc
ldi @while_start_1
mov prl, ra
jmp
while_end_1:
