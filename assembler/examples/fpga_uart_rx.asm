equ SYS_LED_H 0x0C
equ SYS_LED_L 0x00
equ UART_BASE_H 0x09
equ UART_CNTRL_L 0x40 ; {5'b0, TX_EN, RX_EN, UART_EN}
equ UART_BAUDSEL_L 0x20

equ RX_DATA_L 0x00
equ RX_VALID_L 0x01

equ ON_CHAR 65
equ OFF_CHAR 66

; clear sequence
mov prh, zero
mov prl, zero
mov marl, zero
mov marh, zero

ldi $UART_BASE_H
mov marh, ra

ldi $UART_CNTRL_L
mov marl, ra

ldi #0b00000011
mov m, ra ; enable rx and uart

ldi $UART_BAUDSEL_L
mov marl, ra

ldi #2
mov m, ra ; baud_rate = 9600

main_loop:
    ldi @wait_until_message
    mov prl, ra
    ldi $UART_BASE_H
    mov marh, ra
    
    wait_until_message:
        ; read RX if message
        
        ldi $RX_VALID_L
        mov marl, ra ; mem_addr = rx valid
        mov rd, m    ; rd = mem[rx_valid]
        ldi #1
        cmp ra       ; rd == ra
        jne          ; jmp if rx_valid != 1 

        ldi $RX_DATA_L
        mov marl, ra ; mem_addr = rx_data
        mov rd, m    ; rd = mem[rx_data]
        
        ldi $ON_CHAR ; ra = ON_CHAR
        cmp ra       ; rd == ra ; rx_data == ON_CHAR
        
        ldi @led_not_on
        mov prl, ra  ; jmp addr = led_on_not
        jne

        ldi #1
        mov rb, ra

        ldi @set_led_and_return
        mov prl, ra
        jmp

        led_not_on:
            ldi $OFF_CHAR
            cmp ra   ; rd == ra ; rx_data == OFF_CHAR

            ldi @led_not_off
            mov prl, ra
            jne      ; jmp if rx_data != off_char 

            ldi #0
            mov rb, ra
            ldi @set_led_and_return
            mov prl, ra
            jmp
        
        led_not_off:
            ldi @main_loop
            mov prl, ra
            jmp

set_led_and_return: ; rb must be 0x00 or 0x01
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    mov m, rb

    ldi @main_loop
    mov prl, ra
    jmp

