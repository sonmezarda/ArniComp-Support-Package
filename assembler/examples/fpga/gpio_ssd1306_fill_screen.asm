.import "../../lib/oled_soft_i2c.asm" oled_gpio_bus_init, oled_write_command, oled_begin_data_stream, oled_stream_data_byte, oled_end_stream, oled_fill_screen

equ SYS_LED_H         0x0C
equ SYS_LED_L         0x00
equ LED_DONE          0x01

setup:
    mov prh, zero
    mov prl, zero
    mov marl, zero
    mov marh, zero

    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    mov m, zero

    call oled_gpio_bus_init

    ; Basic init.
    ldi #0xAE
    mov rb, ra
    call oled_write_command
    mov rd, rb
    cmp zero
    jne fail

    ; Keep imported function addresses on the stable side of short-LDI
    ; boundaries without perturbing the stack.
    nop
    nop

    ldi #0x8D
    mov rb, ra
    call oled_write_command
    mov rd, rb
    cmp zero
    jne fail
    ldi #0x14
    mov rb, ra
    call oled_write_command
    mov rd, rb
    cmp zero
    jne fail

    ldi #0x20
    mov rb, ra
    call oled_write_command
    mov rd, rb
    cmp zero
    jne fail
    ldi #0x02
    mov rb, ra
    call oled_write_command
    mov rd, rb
    cmp zero
    jne fail

    ldi #0xA4
    mov rb, ra
    call oled_write_command
    mov rd, rb
    cmp zero
    jne fail

    ldi #0xA6
    mov rb, ra
    call oled_write_command
    mov rd, rb
    cmp zero
    jne fail

    ldi #0xAF
    mov rb, ra
    call oled_write_command
    mov rd, rb
    cmp zero
    jne fail

    ; Real GDDRAM fill: write 0xFF to all pages.
    ldi #0xFF
    mov rb, ra
    call oled_fill_screen
    mov rd, rb
    cmp zero
    jne fail

    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    ldi $LED_DONE
    mov m, ra
    jmpa done

fail:
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    mov m, rb

done:
    jmpa done
