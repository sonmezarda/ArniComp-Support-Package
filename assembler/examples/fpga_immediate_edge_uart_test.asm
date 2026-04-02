equ SYS_LED_H 0x0C
equ SYS_LED_L 0x00
equ UART_BASE_H 0x09
equ UART_CNTRL_L 0x40 ; {5'b0, TX_EN, RX_EN, UART_EN}
equ UART_BAUDSEL_L 0x20
equ UART_TX_DATA_L 0x10

equ O_C 'O'
equ K_C 'K'
equ F_C 'F'
equ ONE_C '1'
equ TWO_C '2'
equ THREE_C '3'
equ FOUR_C '4'
equ FIVE_C '5'
equ NEWLINE_C '\n'

equ PASS_LEN 3
equ FAIL_LEN 3

setup:
    ldi #0
    mov prh, ra
    mov prl, ra
    mov marl, ra
    mov marh, ra

    ldi $UART_BASE_H
    mov marh, ra

    ldi $UART_CNTRL_L
    mov marl, ra

    ldi #0b00000101
    mov m, ra ; enable tx and uart

    ldi $UART_BAUDSEL_L
    mov marl, ra

    ldi #2
    mov m, ra ; baud = 9600

; Case 1: 0x1F
case1:
    ldi #0x1F
    mov rd, ra
    ldi #0x1F
    cmp ra

    ldi @case2
    mov prl, ra
    jeq

    ldi $ONE_C
    mov rb, ra
    ldi @fail
    mov prl, ra
    jmp

; Case 2: 0x20
case2:
    ldi #0x20
    mov rd, ra
    ldi #0x20
    cmp ra

    ldi @case3
    mov prl, ra
    jeq

    ldi $TWO_C
    mov rb, ra
    ldi @fail
    mov prl, ra
    jmp

; Case 3: 0x7F
case3:
    ldi #0x7F
    mov rd, ra
    ldi #0x7F
    cmp ra

    ldi @case4
    mov prl, ra
    jeq

    ldi $THREE_C
    mov rb, ra
    ldi @fail
    mov prl, ra
    jmp

; Case 4: 0x80
case4:
    ldi #0x80
    mov rd, ra
    ldi #0x80
    cmp ra

    ldi @case5
    mov prl, ra
    jeq

    ldi $FOUR_C
    mov rb, ra
    ldi @fail
    mov prl, ra
    jmp

; Case 5: 0xFF
case5:
    ldi #0xFF
    mov rd, ra
    ldi #0xFF
    cmp ra

    ldi @pass
    mov prl, ra
    jeq

    ldi $FIVE_C
    mov rb, ra
    ldi @fail
    mov prl, ra
    jmp

pass:
    ldi $NEWLINE_C
    push ra
    ldi $K_C
    push ra
    ldi $O_C
    push ra
    ldi $PASS_LEN
    mov rd, ra

    ldi @send_len_func
    mov prl, ra
    jal

    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    ldi #0x17
    mov m, ra
    hlt
    hlt

fail:
    ldi $NEWLINE_C
    push ra
    push rb
    ldi $F_C
    push ra
    ldi $FAIL_LEN
    mov rd, ra

    ldi @send_len_func
    mov prl, ra
    jal

    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    ldi #0x07
    mov m, ra
    hlt
    hlt

send_len_func:
    ldi $UART_TX_DATA_L
    mov marl, ra

    ldi $UART_BASE_H
    mov marh, ra

send_loop:
    pop rb
    mov m, rb

    subi #1
    mov rd, acc

    ldi @end_loop
    mov prl, ra
    jeq

    ldi @send_loop
    mov prl, ra
    jmp

end_loop:
    mov prl, lrl
    mov prh, lrh
    jmp
