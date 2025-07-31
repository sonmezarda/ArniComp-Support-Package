const x = 2
const y = 2
const s_addr = #0x0F
const counter_addr = #0x0A

ldi s_addr
mov marl, ra

ldi #0 ; ra = 0
mov rd, ra ; rd = 0
add ra ; acc = rd + ra = 0
strl ra ; mem[s_addr] = 0

ldi counter_addr
mov marl, ra
ldi #0
strl ra ; mem[counter_addr] = 0

ldi @sum
mov prl, ra

sum:
    ldi s_addr
    mov marl, ra
    ldrl rd     ; rd = mem[s_addr]
    ldi x       ; ra = x
    add ra      ; acc = mem[s_addr] + x
    strl acc    ; mem[s_addr] = acc

    ldi counter_addr
    mov marl, ra 
    ldrl rd     ; rd = counter

    ldi #1
    add ra      ; acc = counter + 1
    strl acc

    ldi y       ; ra = y
    add ra      ; acc = ra + counter (ra == counter)

    jne

ldi s_addr
mov marl, ra 
ldrl ra
