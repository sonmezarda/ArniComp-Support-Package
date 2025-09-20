ldi #0
mov marl, ra
strl ra
while_start_1:
ldrl rd
ldi #16
mov marh, ra
strh rd
ldi #1
add ra
strl acc
ldi #127
mov rd, ra
add rd
mov rd, acc
sub ml
ldi @if_1
mov prl, ra
jle
ldi #0
strl ra
if_1:
ldi @while_start_1
mov prl, ra
jmp