.import "../lib/math.asm" mul_u8

start:
    ldi #6
    mov rb, ra
    ldi #7
    mov rd, ra
    call mul_u8
done:
    hlt
    hlt
