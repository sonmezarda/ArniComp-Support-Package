ldi #0
mov marl, ra
strl ra
ldi #4
mov marl, ra
ldi #0
strl ra
while_start_1:
ldi #0
mov marl, ra
ldi #32
mov marh, ra
ldrh rd
ldi #1
mov marl, ra
strl rd
ldrl rd
and ra
ldi #2
mov marl, ra
strl acc
and ra
ldi #3
mov marl, ra
strl acc
ldi #1
mov rd, ra
ldi #2
mov marl, ra
sub ml
ldi @if_2
mov prl, ra
jne
ldi #0
mov rd, ra
ldi #4
mov marl, ra
sub ml
ldi @if_1
mov prl, ra
jne
ldi #0
mov marl, ra
ldrl rd
ldi #1
add ra
strl acc
ldi #4
mov marl, ra
ldi #1
strl ra
if_1:
ldi @else_2
mov prl, ra
jmp
if_2:
ldi #2
mov rd, ra
ldi #3
mov marl, ra
sub ml
ldi @if_4
mov prl, ra
jne
ldi #0
mov rd, ra
ldi #4
mov marl, ra
sub ml
ldi @if_3
mov prl, ra
jne
ldi #0
mov marl, ra
ldrl rd
ldi #1
sub ra
strl acc
ldi #4
mov marl, ra
ldi #1
strl ra
if_3:
ldi @else_1
mov prl, ra
jmp
if_4:
ldi #4
mov marl, ra
ldi #0
strl ra
else_1:
else_2:
ldi #0
mov marl, ra
ldrl rd
ldi #16
mov marh, ra
strh rd
ldi @while_start_1
mov prl, ra
jmp