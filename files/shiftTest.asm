const mahmut = 7

ldi @shiftishift
mov prl, ra

ldi #1
mov rd, ra

ldi #0

shiftishift:
    add rd ; acc = rd + rd
    strl acc ; store result in memory

    mov rd, ra ; rd = count
    
    addi #1 ; acc = count + 1
    mov rd, acc ; update count

    ldi mahmut ; a = 3
    add ra ; acc = a + rd (ra == count)

    mov ra, rd ; ra = count
    
    ldrl rd
    jne

ldrl ra




    







