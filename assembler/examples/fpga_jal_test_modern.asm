.include "../includes/uart_constants.inc"

equ SYS_LED_H 0x0C
equ SYS_LED_L 0x00

equ ARDA_LEN 4
equ FPGA_LEN 6

.define PUSH_WITH_RD 1

setup:
    mov prh, zero
    mov prl, zero
    mov marl, zero
    mov marh, zero

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

main:
.if PUSH_WITH_RD
    pushstr "ARDA" :RD
    ldi rd, $ARDA_LEN
    call send_len_func

    pushstr " FPGA\n" :RD
    ldi rd, $FPGA_LEN
    call send_len_func
.else
    pushstr "ARDA"
    ldi rd, $ARDA_LEN
    call send_len_func

    pushstr " FPGA\n"
    ldi rd, $FPGA_LEN
    call send_len_func
.endif

    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    ldi #0x01
    mov m, ra

done: hlt
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

    jeq send_done
    jmp send_loop

send_done: ret :STACK
