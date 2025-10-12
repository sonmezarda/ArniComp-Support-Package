ldi #0
mov marl, ra
ldi #10
mov m, ra
mov rd, ra
cmp m
ldi @if_1
mov prl, ra
jle
ldi @else_1
mov prl, ra
jmp
if_1:
else_1:
ldi #1
mov marl, ra
mov rd, m
ldi #30
add ra
inx
inx
mov m, acc
