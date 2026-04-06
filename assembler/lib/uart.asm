.include "../includes/uart_constants.asm"

.export send_char
.func
send_char: 
    ; rb = char to send
    ldi $UART_BASE_H
    mov marh, ra
    ldi $UART_TX_DATA_L
    mov marl, ra
    mov m, rb
    ret
.endfunc