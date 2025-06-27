ldi #0
mov marh, ra

ldi #2
mov rd, ra



start:
    ldi #0
    out ra
mahmut: 
    ldi @start
    mov prl, ra
    
    add p; acc = rd + p
    jne
    ldi #31
    out ra
    
    ldi @mahmut
    mov prl, ra
    jmp

    