.include "../includes/function_abi.asm"

.export mul_u8
.func
mul_u8:
    ; mul_u8
    ; in :
    ;   RB = a
    ;   RD = b
    ; out:
    ;   RB = a*b (low 8 bits)
    ; clobbers:
    ;   RA, RD, ACC, flags, PRL, PRH
    ; scratch:
    ;   none

    ; Internal layout:
    ;   RA = loop counter (a)
    ;   RB = multiplicand (b)
    ;   RD = running result
    mov ra, rb
    mov rb, rd
    clr rd

mul_u8_check:
    ; PR <- mul_u8_done
    push ra
    ldi LOW(@mul_u8_done)
    mov prl, ra
    ldi HIGH(@mul_u8_done)
    mov prh, ra
    pop ra

    ; if (RA == 0) goto mul_u8_done
    push rd
    mov rd, ra
    cmp zero
    pop rd
    jeq

    ; RD = RD + RB
    add rb
    mov rd, acc

    ; RA = RA - 1
    push rd
    mov rd, ra
    subi #1
    mov ra, acc
    pop rd

    ; PR <- mul_u8_check
    push ra
    ldi LOW(@mul_u8_check)
    mov prl, ra
    ldi HIGH(@mul_u8_check)
    mov prh, ra
    pop ra
    jmp

mul_u8_done:
    mov rb, rd
    ret
.endfunc

.export add_u16_mem
.func
add_u16_mem:
    ; add_u16_mem
    ; in :
    ;   RD = a_lo
    ;   RB = a_hi
    ;   MAR  = address of b_lo
    ;   MAR+1 = address of b_hi
    ; out:
    ;   RD = sum_lo
    ;   RB = sum_hi
    ; clobbers:
    ;   RA, ACC, flags, MARL
    ; scratch:
    ;   none

    add m
    mov ra, acc
    inc #1

    mov rd, rb
    adc m
    mov rb, acc

    mov rd, ra
    ret
.endfunc

.export add_u16_scratch
.func
add_u16_scratch:
    ; add_u16_scratch
    ; in :
    ;   RD = a_lo
    ;   RB = a_hi
    ;   [F_TMP_BASE_H:F_W0_LO_L] = b_lo
    ;   [F_TMP_BASE_H:F_W0_HI_L] = b_hi
    ; out:
    ;   RD = sum_lo
    ;   RB = sum_hi
    ; clobbers:
    ;   RA, ACC, flags, MARL, MARH
    ; scratch:
    ;   none

    ldi $F_TMP_BASE_H
    mov marh, ra
    ldi $F_W0_LO_L
    mov marl, ra

    add m
    mov ra, acc
    inc #1

    mov rd, rb
    adc m
    mov rb, acc

    mov rd, ra
    ret
.endfunc
