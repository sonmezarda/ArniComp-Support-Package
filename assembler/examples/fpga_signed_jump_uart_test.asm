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

equ PASS_LEN 3       ; "OK\n"
equ FAIL_LEN 3       ; "F<n>\n"

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

; Case 1: -1 < 1  => JLT must be taken
case1:
    ldi rd, #0xFF
    ldi #1
    cmp ra

    ldi @case2
    mov prl, ra
    jlt

    ldi $ONE_C
    mov rb, ra
    ldi @fail
    mov prl, ra
    jmp

; Case 2: 1 > -1 => JGT must be taken
case2:
    ldi rd, #1
    ldi #0xFF
    cmp ra

    ldi @case3
    mov prl, ra
    jgt

    ldi $TWO_C
    mov rb, ra
    ldi @fail
    mov prl, ra
    jmp

; Case 3: -128 < 1 => overflowed subtraction, JLT must still be taken
case3:
    ldi rd, #0x80
    ldi #1
    cmp ra

    ldi @case4
    mov prl, ra
    jlt

    ldi $THREE_C
    mov rb, ra
    ldi @fail
    mov prl, ra
    jmp

; Case 4: 127 > -1 => overflowed subtraction, JGT must still be taken
case4:
    ldi rd, #0x7F
    ldi #0xFF
    cmp ra

    ldi @case5
    mov prl, ra
    jgt

    ldi $FOUR_C
    mov rb, ra
    ldi @fail
    mov prl, ra
    jmp

; Case 5: -5 <= -5 and >= -5 => JLE/JGE macros must both work
case5:
    ldi rd, #0xFB
    ldi #0xFB
    cmp ra

    ldi @case5_ge
    mov prl, ra
    jle

    ldi $FIVE_C
    mov rb, ra
    ldi @fail
    mov prl, ra
    jmp

case5_ge:
    ldi @pass
    mov prl, ra
    jge

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
    ldi #0x1F
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
    ldi #0x0F
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
