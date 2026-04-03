.import "../lib/math.asm" add_u16_scratch

.include "../includes/function_abi.asm"

start:
    ; a = 0x1234 -> RD:RB = 0x34:0x12
    ldi #0x34
    mov rd, ra
    ldi #0x12
    mov rb, ra

    ; b = 0x00FF in shared scratch word F_W0
    ldi $F_TMP_BASE_H
    mov marh, ra
    ldi $F_W0_LO_L
    mov marl, ra
    ldi #0xFF
    mov m, ra
    ldi $F_W0_HI_L
    mov marl, ra
    ldi #0x00
    mov m, ra

    call add_u16_scratch

done:
    hlt
    hlt
