; ArniComp Test Program
; Tests various instructions of the new ISA

; Define some constants
equ COUNTER 0x00
equ MAX_COUNT 10
equ DATA_ADDR 0x20

; Main program
start:
    ; Test LDI instruction
    LDI #0x00          ; Load 0 to RA
    
    ; Test MOV instructions
    MOV RD, RA         ; Move RA to RD
    MOV RB, RD         ; Move RD to RB
    MOV MARL, RA       ; Set memory address low
    MOV MARH, RA       ; Set memory address high
    
    ; Test arithmetic operations
    LDI #5             ; Load 5 to RA
    ADD RA             ; Add RA to RD, result in ACC
    SUB RB             ; Subtract RB from RD
    
    ; Test immediate arithmetic
    ADDI #1            ; Add 1 immediate
    SUBI #1            ; Subtract 1 immediate
    
    ; Test logical operations
    XOR RA             ; XOR with RA
    AND RD             ; AND with RD
    NOT ACC            ; NOT ACC
    
    ; Test memory operations
    LDI $DATA_ADDR
    MOV MARL, RA       ; Set address
    LDI #0x7F          ; Max 7-bit value (127)
    MOV M, RA          ; Write to memory
    MOV RA, M          ; Read from memory
    
    ; Test comparison
    CMP RA             ; Compare RA with RD
    
    ; Test special instructions
    SMSBRA             ; Set MSB of RA
    INX                ; Increment MARL
    
loop:
    ; Test conditional jumps
    ADDI #1
    CMP ACC
    JEQ                ; Jump if equal
    JGT                ; Jump if greater
    JLT                ; Jump if less than
    
    ; Unconditional jump back to loop
    ; To jump to a label, need to load address to PRL first
    LDI @loop          ; Load loop address to RA
    MOV PRL, RA        ; Move to program register low
    JMP                ; Jump
    
end:
    HLT                ; Halt the processor
    NOP                ; No operation
