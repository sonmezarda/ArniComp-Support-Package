; ArniComp Sample Program
; This program demonstrates basic functionality

const x = 5
const y = 10

ldi @main
mov prl, ra

ldi #0
mov rd, ra

main:
    ldi $x      ; Load constant x into RA
    add ra      ; Add RA to ACC (ACC = RD + RA)
    
    ldi $y      ; Load constant y into RA  
    add ra      ; Add RA to ACC (ACC = ACC + RA)
    
    ; Store result in memory
    ldi #0
    mov marl, ra
    strl acc
    
    ; Output result
    out acc
    
    ; Simple loop
    mov rd, acc
    ldi #15
    add ra      ; Compare RD with 15
    
    jne         ; Jump back if not equal

; End of program
ldi #0b11111111
