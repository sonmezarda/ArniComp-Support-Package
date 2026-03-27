equ UART_BASE_H 0x09
equ UART_CNTRL_L 0x40 ; {5'b0, TX_EN, RX_EN, UART_EN}
equ UART_BAUDSEL_L 0x20
equ UART_TX_DATA_L 0x10

equ SEND_CHAR 65;

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


mov m, rb
mov m, rb
mov m, rb

HLT
HLT
    

