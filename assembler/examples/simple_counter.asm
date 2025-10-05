; Simple Counter Program
; Counts from 0 to 10 and halts

equ MAX 10

start:
    LDI #0              ; Initialize counter to 0
    MOV RD, RA          ; Store in RD
    
loop:
    ; Increment counter
    ADDI #1             ; Add 1 to ACC
    MOV RD, ACC         ; Update RD with new value
    
    ; Check if we reached MAX
    LDI $MAX
    CMP RA              ; Compare RA (MAX) with RD
    JLT                 ; Jump if RD < MAX
    
    ; If we reach here, counter >= MAX, so halt
    HLT
    
    ; Jump back to loop (this code is reached via JLT)
    LDI @loop
    MOV PRL, RA
    JMP
