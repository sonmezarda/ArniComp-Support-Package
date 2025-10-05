; Comprehensive ISA Test
; Tests all instruction types in the ArniComp ISA

equ MEM_BASE 0x10
equ TEST_VAL 0x55
equ LOOP_COUNT 5

main:
    ; ===== LDI Tests =====
    LDI #0              ; Load 0
    LDI #127            ; Load max 7-bit value
    LDI $TEST_VAL       ; Load constant
    
    ; ===== MOV Tests =====
    ; Basic register moves
    MOV RD, RA          ; RA -> RD
    MOV RB, RD          ; RD -> RB
    MOV RA, ACC         ; ACC -> RA (ACC is source only)
    
    ; Memory address setup
    LDI $MEM_BASE
    MOV MARL, RA        ; Set memory address low
    LDI #0
    MOV MARH, RA        ; Set memory address high
    
    ; Memory operations
    LDI #42
    MOV M, RA           ; Write to memory
    MOV RB, M           ; Read from memory
    
    ; Program counter operations
    MOV RD, PCL         ; Read program counter
    MOV RA, PCH         ; Read program counter high
    
    ; ===== Arithmetic Tests =====
    LDI #10
    MOV RD, RA          ; RD = 10
    LDI #5
    ADD RA              ; ACC = 5 + 10 = 15
    
    SUB RB              ; ACC = RD - RB
    ADC RA              ; ACC = RD + RA + carry
    SBC M               ; ACC = RD - M - carry
    
    ; Immediate arithmetic
    ADDI #1             ; ACC += 1
    ADDI #7             ; ACC += 7 (max)
    SUBI #2             ; ACC -= 2
    SUBI #7             ; ACC -= 7 (max)
    
    ; ===== Logical Tests =====
    LDI #0b01010101
    MOV RD, RA
    
    AND RA              ; ACC = RD & RA
    XOR RB              ; ACC = RD XOR RB
    NOT RA              ; ACC = ~RA
    NOT RD              ; ACC = ~RD
    NOT ACC             ; ACC = ~ACC
    
    ; ===== Comparison Tests =====
    LDI $LOOP_COUNT
    CMP RA              ; Compare RA with RD
    CMP M               ; Compare M with RD
    CMP ACC             ; Compare ACC with RD
    
    ; ===== Special Instructions =====
    SMSBRA              ; Set MSB of RA
    INX                 ; Increment MARL
    NOP                 ; No operation
    
    ; ===== Jump Tests =====
test_jumps:
    LDI #20
    MOV RD, RA
    LDI #20
    CMP RA
    JEQ                 ; Should jump (20 == 20)
    
after_jeq:
    LDI #15
    CMP RA              ; Compare 15 with 20
    JLT                 ; Should jump (15 < 20)
    
after_jlt:
    LDI #25
    CMP RA              ; Compare 25 with 20
    JGT                 ; Should jump (25 > 20)
    
after_jgt:
    LDI #20
    CMP RA              ; Compare 20 with 20
    JGE                 ; Should jump (20 >= 20)
    
after_jge:
    LDI #15
    CMP RA              ; Compare 15 with 20
    JLE                 ; Should jump (15 <= 20)
    
after_jle:
    LDI #25
    CMP RA              ; Compare 25 with 20
    JNE                 ; Should jump (25 != 20)
    
after_jne:
    ; Test unconditional jump
    LDI @end
    MOV PRL, RA
    JMP                 ; Jump to end
    
    ; This should never execute
    HLT
    
end:
    ; Program complete
    HLT
