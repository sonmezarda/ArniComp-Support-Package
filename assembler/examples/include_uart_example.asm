.include "../includes/uart.inc"

setup_uart:
    ldi $UART_BASE_H
    mov marh, ra

    ldi $UART_CONTROL_L
    mov marl, ra
    ldi $UART_ENABLE_TX
    mov m, ra

    ldi $UART_BAUDSEL_L
    mov marl, ra
    ldi $UART_BAUD_9600
    mov m, ra

send_a:
    ldi $UART_TX_DATA_L
    mov marl, ra
    ldi 'A'
    mov m, ra

done:
    hlt
    hlt
