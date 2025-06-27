const a = 20


ldi label1
mov prl, ra


ldi #0
mov rd, ra
ldi #1
add ra ; acc = 1

label1:
    ldi #1
    add ra ; acc = rd + 1

    mov rd, acc ; rd = rd + 1 (acc) 
    ldi #8 ; ra = 8
    add ra ; acc = ra + rd (flags setted)
    
    jne

ldi #0b1010101