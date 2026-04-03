; Memory + PUSH MAR regression

    ; Start at address 0x0123 so MARH restore is visible too.
    LDI #0x23
    MOV MARL, RA
    LDI #0x01
    MOV MARH, RA

    ; Save full MAR on stack using the PUSH-only remap.
    PUSH MARL
    PUSH MARH

    ; Clobber MAR completely.
    CLR RA
    MOV MARL, RA
    MOV MARH, RA

    ; Restore MAR from stack and use it for normal memory accesses.
    POP MARH
    POP MARL

    LDI #0x55
    MOV M, RA
    MOV RB, M

    INC #1

    LDI #0x55
    NOT RA
    MOV M, ACC
    MOV RD, M

    HLT
    HLT
