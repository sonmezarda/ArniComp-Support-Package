equ SYS_LED_H 0x0C
equ SYS_LED_L 0x00
equ UART_BASE_H 0x09
equ UART_CNTRL_L 0x40 ; {5'b0, TX_EN, RX_EN, UART_EN}
equ UART_BAUDSEL_L 0x20
equ UART_TX_DATA_L 0x10

equ A_C 'A'
equ B_C 'B'
equ ENDSTR_C '\0'

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

main:
    ldi $ENDSTR_C
    push ra
    ldi $B_C
    push ra
    ldi $A_C
    push ra

    ldi $UART_TX_DATA_L
    mov marl, ra

    ldi $UART_BASE_H
    mov marh, ra
    ldi rd, $ENDSTR_C

send_loop:
    pop rb
    cmp rb

    ldi @done
    mov prl, ra
    jeq

    mov m, rb

    ldi @send_loop
    mov prl, ra
    jmp

done:
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    ldi #0x2A
    mov m, ra
    hlt
    hlt
