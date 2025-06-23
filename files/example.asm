const i1 = #0x11
ldi #10

mov rd, ra
ldi i1

add ra
mov rd, acc

ldi label1
mov prl, ra
jmp 

ldi #0x02

label1:
   mov prl, ra
   jmp