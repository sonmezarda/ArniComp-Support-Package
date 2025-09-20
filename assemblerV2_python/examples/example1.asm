ldi #0
mov marl, ra
strl ra
while_start_1:
while_start_2:
ldi #127
mov rd, ra
add rd
mov rd, acc
sub ml
ldi @while_end_2
mov prl, ra
jge
ldrl rd
ldi #1
add ra
mov marl, acc
strl rd
add ra
ldi #0
mov marl, ra
strl acc
ldi @while_start_2
mov prl, ra
jmp
while_end_2:
ldi #0
mov marl, ra
strl ra
while_start_3:
ldi #127
mov rd, ra
add rd
mov rd, acc
sub ml
ldi @while_end_3
mov prl, ra
jge
ldrl rd
ldi #1
add ra
mov marl, acc
ldi #0
strl ra
ldi #1
add ra
ldi #0
mov marl, ra
strl acc
ldi @while_start_3
mov prl, ra
jmp
while_end_3:
ldi #0
mov marl, ra
strl ra
ldi @while_start_1
mov prl, ra
jmp