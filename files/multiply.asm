const x = 9
const y = 12
const caddr = 0
const resaddr = 1

ldi #0
mov rd, ra
ldi $caddr
mov marl, ra
ldi $y
strl ra     ; MEM[marl] = y

ldi $resaddr
mov marl, ra
strl rd


ldi @mult
mov prl, ra

; Clear registers
ldi #0      ; ra  = 0
mov rd, ra  ; rd  = 0
add ra      ; acc = 0


mult:
    ldi $x       ; ra = x
    mov rd, ra   ; rd = x
    ldi $resaddr    
    mov marl, ra
    ldrl ra      ; ra = MEM[resaddr]
    add ra       ; acc = rd + ra
    strl acc
    
    ldi $caddr
    mov marl, ra
    ldrl rd      ; rd = MEM[marl] (counter)
    subi #1      ; acc = rd - 1 (counter - 1)
    strl acc
    
    jne
    
ldi $resaddr
mov marl, ra
ldrl rd
