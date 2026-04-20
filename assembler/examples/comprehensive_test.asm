; Comprehensive ISA / assembler smoke test
; Keeps the program runnable while touching the major real instructions
; and commonly used pseudoinstructions in the final ISA.

equ MEM_BASE   0x10
equ TEST_VAL   0x55
equ TEST_VAL2  0x2A
equ LOOP_COUNT 3

main:
    ; ===== Load tests =====
    LDL RA, #5
    LDL RD, $TEST_VAL[4:0]
    LDH RA, #7
    LDH RD, $TEST_VAL[7:5]

    LDI #0
    MOV RD, RA
    LDI #127
    MOV RB, RA
    LDI $TEST_VAL
    LDI RD, $TEST_VAL2
    LDI RA, LOW(@*after_target_load)
*after_target_load:

    ; ===== MOV / memory tests =====
    LDI #0
    MOV MARH, RA
    LDI $MEM_BASE
    MOV MARL, RA

    LDI $TEST_VAL
    MOV M, RA
    MOV RB, M
    MOV RA, ZERO
    MOV RD, RB
    MOV RA, ACC
    MOV PRH, ZERO
    MOV PRL, ZERO

    ; ===== Arithmetic / logic tests =====
    LDI #10
    MOV RD, RA
    LDI #5
    ADD RA
    SUB RB
    ADC RA
    SBC M

    ADDI #1
    ADDI #7
    SUBI #2
    SUBI #7

    LDI #0b01010101
    MOV RD, RA
    AND RA
    XOR RB
    NOT RA
    NOT RD
    NOT ACC

    ; ===== Comparison tests =====
    LDI $LOOP_COUNT
    MOV RD, RA
    CMP RA
    CMP M
    CMP ACC

    ; ===== Stack tests =====
    PUSH RA
    PUSH RD
    PUSH RB
    PUSH ACC
    PUSH MARL
    PUSH MARH
    POP RA
    POP RD
    POP RB
    POP MARH
    POP MARL
    POP PRH

    PUSHI #0x11
    PUSHI #0x22 :RD
    POP RD
    POP RA

    PUSHSTR "OK"
    POP RB
    POP RD

    ; ===== Address increment / decrement tests =====
    LDI #0
    MOV MARH, RA
    LDI $MEM_BASE
    MOV MARL, RA
    INC #1
    INC #2
    DEC #1
    DEC #2

    ; ===== Direct jump opcode tests =====
    LDI LOW(@*after_jeq)
    MOV PRL, RA
    LDI HIGH(@*after_jeq)
    MOV PRH, RA
    JEQ

*after_jeq:
    LDI LOW(@*after_jne)
    MOV PRL, RA
    LDI HIGH(@*after_jne)
    MOV PRH, RA
    JNE

*after_jne:
    LDI LOW(@*after_jcs)
    MOV PRL, RA
    LDI HIGH(@*after_jcs)
    MOV PRH, RA
    JCS

*after_jcs:
    LDI LOW(@*after_jcc)
    MOV PRL, RA
    LDI HIGH(@*after_jcc)
    MOV PRH, RA
    JCC

*after_jcc:
    LDI LOW(@*after_jmi)
    MOV PRL, RA
    LDI HIGH(@*after_jmi)
    MOV PRH, RA
    JMI

*after_jmi:
    LDI LOW(@*after_jvs)
    MOV PRL, RA
    LDI HIGH(@*after_jvs)
    MOV PRH, RA
    JVS

*after_jvs:
    LDI LOW(@*after_jlt)
    MOV PRL, RA
    LDI HIGH(@*after_jlt)
    MOV PRH, RA
    JLT

*after_jlt:
    LDI LOW(@*after_jgt)
    MOV PRL, RA
    LDI HIGH(@*after_jgt)
    MOV PRH, RA
    JGT

*after_jgt:
    NOP

    ; ===== Target-taking jump / alias tests =====
    JEQ @*branch_eq
    JNE @*branch_ne
    JZ @*branch_z
    JNZ @*branch_nz
    JC @*branch_c
    JNC @*branch_nc
    JN @*branch_n
    JV @*branch_v
    JGEU @*branch_geu
    JLTU @*branch_ltu
    JLTS @*branch_lts
    JMP @*after_jump_macros

*branch_eq:
    JMP @*after_jump_macros
*branch_ne:
    JMP @*after_jump_macros
*branch_z:
    JMP @*after_jump_macros
*branch_nz:
    JMP @*after_jump_macros
*branch_c:
    JMP @*after_jump_macros
*branch_nc:
    JMP @*after_jump_macros
*branch_n:
    JMP @*after_jump_macros
*branch_v:
    JMP @*after_jump_macros
*branch_geu:
    JMP @*after_jump_macros
*branch_ltu:
    JMP @*after_jump_macros
*branch_lts:
    JMP @*after_jump_macros

*after_jump_macros:
    JLE @*after_jle
*after_jle:
    JGE @*after_jge
*after_jge:
    JLEU @*after_jleu
*after_jleu:
    JGTU @*after_jgtu :RD
*after_jgtu:

    ; ===== Call / return tests =====
    CALL @*leaf_worker
    CALL @*leaf_worker :RD
    CALL @*non_leaf_worker

    ; ===== Absolute jump pseudoinstruction =====
    JMPA @*done

*leaf_worker:
    MOV RD, LRL
    MOV RB, LRH
    RET

*non_leaf_worker:
    PUSH LRL
    PUSH LRH
    CALL @*leaf_worker
    RET :STACK

*done:
    HLT
