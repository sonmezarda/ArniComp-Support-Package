equ SYS_LED_H 0x0C
equ SYS_LED_L 0x00
equ UART_BASE_H 0x09
equ UART_CNTRL_L 0x40 ; {5'b0, TX_EN, RX_EN, UART_EN}
equ UART_BAUDSEL_L 0x20
equ UART_TX_DATA_L 0x10

equ O_C 'O'
equ K_C 'K'
equ E_C 'E'
equ R_C 'R'
equ A_C 'A'
equ B_C 'B'
equ C_C 'C'

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
    ; Seed RD with zero once, then stress control flow and other registers.
    ldi rd, #0

    ldi $A_C
    mov rb, ra
    ldi $B_C
    mov ra, rb
    ldi $C_C
    mov rb, ra

    ldi @skip_1
    mov prl, ra
    jmp
    ldi #'X'
    mov m, ra

skip_1:
    ldi @skip_2
    mov prl, ra
    jmp
    ldi #'Y'
    mov m, ra

skip_2:
    ldi #0
    cmp ra ; compare current RA=0 against persistent RD=0

    ldi @fail
    mov prl, ra
    jne

pass:
    ldi $K_C
    push ra
    ldi $O_C
    push ra
    ldi #2
    mov rd, ra

    ldi @send_len_func
    mov prl, ra
    jal

    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    ldi #0x12
    mov m, ra
    hlt
    hlt

fail:
    ldi $R_C
    push ra
    ldi $E_C
    push ra
    ldi #2
    mov rd, ra

    ldi @send_len_func
    mov prl, ra
    jal

    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    ldi #0x21
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
