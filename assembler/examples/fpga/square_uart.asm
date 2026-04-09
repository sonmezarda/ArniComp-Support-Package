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

        call get_3_digit ; stack top: ones, then tens, then hundreds

        pop rb ; ones
        pop ra ; tens
        pop rd ; hundreds
        push rb ; keep ones for later
        push ra ; keep tens for later

        ldi $UART_TX_DATA_L
        mov marl, ra

        call number_to_ascii_func
        mov m, rb

        pop rd ; tens
        call number_to_ascii_func
        mov m, rb

        pop rd ; ones
        call number_to_ascii_func
        mov m, rb

        jmp main_loop



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

get_3_digit:
; rb = 1 byte unsigned number
; pushes hundreds, tens, ones to stack
    mov rd, rb
    mov rb, zero ; rb = counter
    get_3_digit_loop:
        ldi #100
        cmp ra ; ra, rd

        jltu get_3_digit_exit
        
        ; sub 100 and count
        ldi #100
        sub ra   ; acc = rd - ra ; number-100
        push acc ; acc = rd - 100 ; new number
        mov rd, rb
        addi #1  ; acc = rb + 1
        mov rb, acc ; rb = rb + 1
        pop rd      ; rd = new number

        jmp get_3_digit_loop

    get_3_digit_exit:
        push rb ; rb = 100 count
        mov rb, zero
    get_2_digit_loop:
        ldi #10
        cmp ra  

        jltu get_2_digit_exit


        ; sub 10 and count
        ldi #10
        sub ra
        push acc    ; acc = rd - 10 ; new number
        mov rd, rb
        addi #1
        mov rb, acc ; rb = rb + 1
        pop rd      ; rd = new number
        jmp get_2_digit_loop

    get_2_digit_exit:
        push rb ; rb = 10 count
        push rd ; rd = remainder (1 count)

    ret

