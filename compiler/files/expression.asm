ldi #0
mov marl, ra
mov m, ra
inx
ldi #1
mov m, ra
inx
ldi #5
mov m, ra
inx
ldi #6
mov m, ra
ldi #2
mov marl, ra
mov rd, m
ldi #1
mov marl, ra
add m
mov rd, acc
sub m
mov rd, acc
ldi #20
add ra
ldi #4
mov marl, ra
mov m, acc
