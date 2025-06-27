ldi jumpijump
mov prl , ra

ldi #5
mov rd, ra

ldi #10
add ra ; acc = 15

mov ra, acc


jumpijump: 
    ldi #3
    add ra ; acc = 18

    ldi #6
    add ra

    jne jumpijump ; acc != 24, so jump
