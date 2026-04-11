.import "../../lib/oled_soft_i2c.asm" oled_gpio_bus_init, oled_write_command, oled_init_basic

equ SYS_LED_H         0x0C
equ SYS_LED_L         0x00
equ LED_STAGE0        0x3F
equ LED_DONE          0x01

setup:
    mov prh, zero
    mov prl, zero
    mov marl, zero
    mov marh, zero

    ; Clear status LED.
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    mov m, zero

    ; Show that the program started at all.
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    ldi $LED_STAGE0
    mov m, ra

    ; Prepare gpio[0]/gpio[1] for software open-drain I2C.
    call oled_gpio_bus_init

    ; Run the basic OLED init sequence from the soft-I2C library.
    call oled_init_basic
    mov rd, rb
    cmp zero
    jne fail

    ; Show "done".
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    ldi $LED_DONE
    mov m, ra

fail:
    ; On failure, show the non-zero OLED error code directly.
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    mov m, rb

done:
    jmpa done
