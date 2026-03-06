ldi #50
mov rd, ra

ldi #100

cmp ra
ldi @greater
mov prl, ra

jgt

ldi #10

ldi @end
mov prl, ra
jmp

greater:
    ldi #1
    mov ra, rb
    ldi @end
    mov prl, ra
    jmp

end:
    hlt