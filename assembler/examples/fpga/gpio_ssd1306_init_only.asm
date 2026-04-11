.import "../../lib/oled_soft_i2c.asm" oled_gpio_bus_init, oled_write_stack_noack, oled_write_command_noack

equ SYS_LED_H         0x0C
equ SYS_LED_L         0x00
equ LED_STAGE0        0x3F
equ LED_STAGE1        0x01
equ LED_STAGE2        0x03
equ LED_STAGE3        0x07
equ LED_STAGE4        0x0F
equ LED_STAGE5        0x1F
equ LED_DONE          0x3F

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

    ; Display off.
    ldi #0xAE
    mov rb, ra
    call oled_write_command_noack
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    ldi $LED_STAGE1
    mov m, ra

    ; Charge pump command + enable.
    ldi #0x14
    push ra
    ldi #0x8D
    push ra
    ldi #2
    mov rb, ra
    ldi #0x00
    mov rd, ra
    call oled_write_stack_noack
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    ldi $LED_STAGE2
    mov m, ra

    ; Addressing mode command + page addressing mode.
    ldi #0x02
    push ra
    ldi #0x20
    push ra
    ldi #2
    mov rb, ra
    ldi #0x00
    mov rd, ra
    call oled_write_stack_noack
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    ldi $LED_STAGE3
    mov m, ra

    ; Resume GDDRAM display, normal display, display on.
    ldi #0xAF
    push ra
    ldi #0xA6
    push ra
    ldi #0xA4
    push ra
    ldi #3
    mov rb, ra
    ldi #0x00
    mov rd, ra
    call oled_write_stack_noack
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    ldi $LED_STAGE4
    mov m, ra

    ; Show "done".
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    ldi $LED_DONE
    mov m, ra

done:
    jmpa done
