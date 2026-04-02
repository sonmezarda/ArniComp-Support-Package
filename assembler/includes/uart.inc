; UART memory map constants for ArniComp examples

equ UART_BASE_H 0x09

; Low-byte register offsets
equ UART_RX_DATA_L         0x00
equ UART_RX_VALID_L        0x01
equ UART_RX_BUSY_L         0x02
equ UART_FRAMING_ERROR_L   0x03
equ UART_RX_OVERFLOW_L     0x04

equ UART_TX_DATA_L         0x10
equ UART_TX_READY_L        0x11
equ UART_TX_BUSY_L         0x12
equ UART_TX_EMPTY_L        0x13

equ UART_BAUDSEL_L         0x20

equ UART_STATUS_L          0x30
; STATUS register bit layout:
; {1'b0, RX_OVERFLOW, TX_EMPTY, TX_BUSY, TX_READY, FRAMING_ERROR, RX_BUSY, RX_VALID}

equ UART_CONTROL_L         0x40
; CONTROL register bit layout: {3'b0, CLEAR_ERROR_ADDR, CLEAR_RX_ADDR, TX_EN, RX_EN, UART_EN}

equ UART_EN_L              0x41
equ UART_RX_EN_L           0x42
equ UART_TX_EN_L           0x43
equ UART_RX_CLEAR_L        0x44
equ UART_CLEAR_ERROR_L     0x45

equ UART_ENABLE_TX   0b00000101
equ UART_ENABLE_RX   0b00000011
equ UART_ENABLE_BOTH 0b00000111

equ UART_BAUD_9600   2
