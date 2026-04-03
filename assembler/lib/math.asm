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
