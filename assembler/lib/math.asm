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
    ; vregs:
    ;   none

    ; Internal layout:
    ;   RA = loop counter (a)
    ;   RB = multiplicand (b)
    ;   RD = running result
    mov ra, rb
    mov rb, rd
    clr rd

*loop:
    ; PR <- mul_u8_done
    push ra
    ldi LOW(@*done)
    mov prl, ra
    ldi HIGH(@*done)
    mov prh, ra
    pop ra

    ; if (RA == 0) goto *done
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

    ; PR <- *loop
    push ra
    ldi LOW(@*loop)
    mov prl, ra
    ldi HIGH(@*loop)
    mov prh, ra
    pop ra
    jmp

*done:
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
    ; vregs:
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
    ;   [F_VR_BASE_H:F_VT8_L] = b_lo
    ;   [F_VR_BASE_H:F_VT9_L] = b_hi
    ; out:
    ;   RD = sum_lo
    ;   RB = sum_hi
    ; clobbers:
    ;   RA, ACC, flags, MARL, MARH
    ; vregs:
    ;   none

    ldi $F_VR_BASE_H
    mov marh, ra
    ldi $F_VT8_L
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
