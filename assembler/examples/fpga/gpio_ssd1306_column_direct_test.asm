; Direct SSD1306 page/column command test using software I2C on GPIO pins.
;
; This test bypasses oled_set_page_column completely.
; It sends the column-select commands directly:
; - Page 0, column 0x70, data 0xFF
; - Page 1, column 0x60, data 0xFF
;
; Visible LED result:
; - 0x01 -> success
; - 0x02 -> address NACK
; - 0x03 -> control-byte NACK
; - 0x04 -> command-byte NACK
; - 0x05 -> data-byte NACK

.import "../../lib/oled_soft_i2c.asm" oled_gpio_bus_init, oled_write_command, oled_begin_data_stream, oled_stream_data_byte, oled_end_stream, oled_init_basic, oled_fill_screen

equ SYS_LED_H         0x0C
equ SYS_LED_L         0x00
equ LED_OK            0x01

setup:
    mov prh, zero
    mov prl, zero
    mov marl, zero
    mov marh, zero

    ; Clear visible LEDs.
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    mov m, zero

    call oled_gpio_bus_init

    call oled_init_basic
    mov rd, rb
    cmp zero
    jne fail

    ; Clear the whole screen first so only the two probe bytes remain.
    mov rb, zero
    call oled_fill_screen
    mov rd, rb
    cmp zero
    jne fail

    ; Page 0, column 0x70.
    ldi #0xB0
    mov rb, ra
    call oled_write_command
    mov rd, rb
    cmp zero
    jne fail

    ldi #0x00
    mov rb, ra
    call oled_write_command
    mov rd, rb
    cmp zero
    jne fail

    ldi #0x17
    mov rb, ra
    call oled_write_command
    mov rd, rb
    cmp zero
    jne fail

    call oled_begin_data_stream
    mov rd, rb
    cmp zero
    jne fail

    ldi #0xFF
    mov rb, ra
    call oled_stream_data_byte
    mov rd, rb
    cmp zero
    jne fail

    call oled_end_stream
    mov rd, rb
    cmp zero
    jne fail

    ; Page 1, column 0x60.
    ldi #0xB1
    mov rb, ra
    call oled_write_command
    mov rd, rb
    cmp zero
    jne fail

    ldi #0x00
    mov rb, ra
    call oled_write_command
    mov rd, rb
    cmp zero
    jne fail

    ldi #0x16
    mov rb, ra
    call oled_write_command
    mov rd, rb
    cmp zero
    jne fail

    call oled_begin_data_stream
    mov rd, rb
    cmp zero
    jne fail

    ldi #0xFF
    mov rb, ra
    call oled_stream_data_byte
    mov rd, rb
    cmp zero
    jne fail

    call oled_end_stream
    mov rd, rb
    cmp zero
    jne fail

success:
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    ldi $LED_OK
    mov m, ra
    jmpa done

fail:
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    mov m, rb
    jmpa done

done:
    jmpa done
