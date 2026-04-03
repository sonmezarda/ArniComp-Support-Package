.include "../includes/uart_constants.asm"
.import "../lib/math.asm" mul_u8

equ NUMBER_OFFSET 0x30
; gets 1 byte number from uart. returns number^2

setup:
    mov prh, zero
    mov prl, zero
    mov marl, zero
    mov marh, zero

    ldi $UART_BASE_H
    mov marh, ra

    ldi $UART_CONTROL_L
    mov marl, ra

    ldi #0b00000111
    mov m, ra ; enable rx tx and uart

    ldi $UART_BAUDSEL_L
    mov marl, ra

    ldi #2
    mov m, ra ; baud_rate = 9600

main_loop:
    ldi @wait_until_msg
    mov prl, ra
    ldi $UART_BASE_H
    mov marh, ra

    wait_until_msg:
        ; read RX if message
        ldi $UART_RX_VALID_L
        mov marl, ra ; mem_addr = rx valid
        mov rd, m    ; rd = mem[rx_valid]
        ldi #1
        cmp ra       ; rd == ra
        jne          ; jmp if rx_valid != 1 

        ldi $UART_RX_DATA_L
        mov marl, ra ; mem_addr = rx_data
        mov rd, m    ; rd = mem[rx_data]

        call ascii_to_number_func ; rb = rd - '0'

        mov rd, rb
        ldi #10
        cmp ra
        jgeu main_loop
        
        mov rd, rb
        call mul_u8 ; rb = rd*rb

        mov rd, rb
        call number_to_ascii_func ; rb = ascii to send

        mov rd, rb
        call send_char

        jmp main_loop


send_char: ; rd = char to send
    ldi $UART_TX_DATA_L
    mov marl, ra
    mov m, rd

    ret

ascii_to_number_func: 
; rd = ascii to convert; rb = return number (converted number)
; if rb > 9 invalid result
    ldi $NUMBER_OFFSET
    sub ra ; acc = rd - ra
    mov rb, acc
    ret

number_to_ascii_func: 
; rd = number to convert; rb = return ascii (converted number)
    ldi $NUMBER_OFFSET
    add ra ; acc = rd - ra
    mov rb, acc
    ret


