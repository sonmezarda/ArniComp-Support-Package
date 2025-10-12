ldi #0
mov marl, ra
mov m, ra
ldi #1
mov rd, ra
inx
inx
cmp m
ldi @if_1
mov prl, ra
jne
ldi #0
mov marl, ra
mov rd, m
addi #1
mov m, acc
if_1:
