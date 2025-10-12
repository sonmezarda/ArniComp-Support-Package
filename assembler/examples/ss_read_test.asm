equ SS_H 0x10
equ SS_L 0x00
equ BUTTON_H 0x20
equ BUTTON_L 0x00

equ B1_MASK 0b1
equ B2_MASK 0b10

ldi #0
mov rb, ra ; rb = 0

loop:

    ldi $BUTTON_H
    mov marh, ra
    mov rd, m ; rd = Buttons state
    
    ldi $B1_MASK
    and ra ; acc = Buttons state & B1_MASK

    ldi #0
    mov rd, ra ; rd = 0

    cmp acc ; compare acc with 0

    ldi @no_b1_press
    mov prl, ra
    jeq  ; if acc == 0 jump to no_b1_press

    ; Button 1 pressed rb = rb + 1
    mov rd, rb
    addi #1 ; acc = rb + 1
    mov rb, acc ; rb = acc (rb = rb + 1)


    ldi $SS_H
    mov marh, ra
    mov m, rb ; SS = rb

    no_b1_press:

        ldi @loop
        mov prl, ra
        jmp


hlt