equ SYS_LED_H 0x0C
equ SYS_LED_L 0x00
equ UART_BASE_H 0x09
equ UART_CNTRL_L 0x40 ; {5'b0, TX_EN, RX_EN, UART_EN}
equ UART_BAUDSEL_L 0x20
equ UART_TX_DATA_L 0x10
equ UART_TX_READY_L 0x11

equ A_C 'A'
equ R_C 'R'
equ D_C 'D'
equ N_C 'N'
equ I_C 'I'
equ NEWLINE_C '\n'
equ SPACE_C ' '
equ ARDA_LEN 4
equ NIDA_LEN 6

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
    mov m, ra ; baud_rate = 9600


main:
    ldi $A_C
    push ra
    ldi $D_C
    push ra
    ldi $R_C
    push ra
    ldi $A_C
    push ra
    ldi $ARDA_LEN
    mov rd, ra

    ldi @send_str_func
    mov prl, ra
    jal

    ldi $NEWLINE_C
    push ra
    ldi $A_C
    push ra
    ldi $D_C
    push ra
    ldi $I_C
    push ra
    ldi $N_C
    push ra
    ldi $SPACE_C
    push ra
    ldi $NIDA_LEN
    mov rd, ra

    ldi @send_str_func
    mov prl, ra
    jal

    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra

    ldi #0xff
    mov m, ra
    
    HLT
    HLT


send_str_func: ; str must be in the stack with reverse order
    
    ldi $UART_TX_DATA_L
    mov marl, ra

    ldi $UART_BASE_H
    mov marh, ra
    send_loop:
        pop rb
        mov m, rb ; send rb to uart

        subi #1
        mov rd, acc
        
        ldi @end_loop
        mov prl, ra
        jeq    ; count reached zero ? end_loop

        ldi @send_loop
        mov prl, ra
        jmp

    end_loop:
        mov prl, lrl
        mov prh, lrh
        jmp
