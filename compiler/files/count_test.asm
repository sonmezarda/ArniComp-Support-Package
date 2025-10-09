ldi #0
mov marl, ra
mov m, ra
ldi #4
mov marl, ra
ldi #0
mov m, ra
while_start_1:
mov marl, ra
ldi #32
mov marh, ra
mov rd, m
inx
mov m, rd
mov rd, m
ldi #1
and ra
inx
mov m, acc
ldi #2
and ra
inx
mov m, acc
ldi #1
mov rd, ra
ldi #2
mov marl, ra
cmp m
ldi @if_3
mov prl, ra
jne
ldi #0
mov rd, ra
inx
cmp m
ldi @if_1
mov prl, ra
jne
mov marl, ra
mov rd, m
addi #1
mov m, acc
ldi #4
mov marl, ra
ldi #1
mov m, ra
if_1:
ldi @else_1
mov prl, ra
jmp
if_3:
ldi #2
mov rd, ra
ldi #3
mov marl, ra
cmp m
ldi @if_4
mov prl, ra
jne
ldi #0
mov rd, ra
ldi #4
mov marl, ra
cmp m
ldi @if_2
mov prl, ra
jne
mov marl, rd
mov rd, m
ldi #1
sub ra
mov m, acc
ldi #4
mov marl, ra
ldi #1
mov m, ra
if_2:
ldi @else_1
mov prl, ra
jmp
if_4:
ldi #4
mov marl, ra
ldi #0
mov m, ra
else_1:
ldi #0
mov marl, ra
mov rd, m
ldi #16
mov marh, ra
mov m, rd
ldi @while_start_1
mov prl, ra
jmp
