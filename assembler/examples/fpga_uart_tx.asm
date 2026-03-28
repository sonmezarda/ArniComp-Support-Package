equ UART_BASE_H 0x09
equ UART_CNTRL_L 0x40 ; {5'b0, TX_EN, RX_EN, UART_EN}
equ UART_BAUDSEL_L 0x20
equ UART_TX_DATA_L 0x10
equ UART_TX_READY_L 0x11

equ SEND_CHAR 65

;clear sequence
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

ldi $UART_TX_DATA_L
mov marl, ra
ldi $SEND_CHAR
mov rb, ra

ldi #1
mov rd, ra


ldi @wait_until_ready
mov prl, ra

wait_until_ready:
    
    ldi $UART_TX_READY_L
    mov marl, ra
    mov ra, m ; ra = TX_READY
    cmp ra    ; rd cmp rd (rd=1)
    jne       ; jmp if ra != 1

    ldi $UART_TX_DATA_L
    mov marl, ra
    mov m, rb
    jmp

HLT
HLT
    

