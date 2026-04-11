; Minimal SSD1306 movement scratch test using shared soft-I2C OLED library.
;
; This test:
; - initializes the OLED
; - clears the whole screen with GDDRAM writes
; - writes one 0xFF byte to page 0, column 0x70
; - writes one 0xFF byte to page 1, column 0x60
;
; Visible LED result:
; - 0x01 -> success
; - otherwise RB error code from the OLED library path

.import "../../lib/oled_soft_i2c.asm" oled_gpio_bus_init, oled_write_command, oled_set_page_column_direct, oled_begin_data_stream, oled_stream_data_byte, oled_end_stream, oled_init_basic, oled_fill_screen, oled_draw_square, oled_clear_square

equ SYS_LED_H         0x0C
equ SYS_LED_L         0x00
equ LED_OK            0x01

equ GPIO_BASE_H       0x08
equ BUTTON_GPIO_DIR_L 0x32
equ BUTTON_GPIO_IN_L  0x12
equ BUTTON_DEBOUNCE   0x80

equ SQ_COL_ADDR_H     0x00
equ SQ_COL_ADDR_L     0x20
 
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

    call oled_init_basic
    mov rd, rb
    cmp zero
    jne fail

    ; Clear the whole screen first.
    mov rb, zero
    call oled_fill_screen
    mov rd, rb
    cmp zero
    jne fail

main_loop:

*wait_until_idle:
    ldi $GPIO_BASE_H
    mov marh, ra
    ldi $BUTTON_GPIO_IN_L
    mov marl, ra
    mov rd, m
    cmp zero
    jne *wait_until_idle

    call debounce_delay
    ldi $GPIO_BASE_H
    mov marh, ra
    ldi $BUTTON_GPIO_IN_L
    mov marl, ra
    mov rd, m
    cmp zero
    jne *wait_until_idle

*wait_until_button:
    ldi $GPIO_BASE_H
    mov marh, ra
    ldi $BUTTON_GPIO_IN_L
    mov marl, ra

    mov rd, m
    cmp zero
    jeq *wait_until_button

    call debounce_delay
    ldi $GPIO_BASE_H
    mov marh, ra
    ldi $BUTTON_GPIO_IN_L
    mov marl, ra
    mov rd, m
    cmp zero
    jeq *wait_until_button

    ; button pressed 

    ldi $SQ_COL_ADDR_H
    mov marh, ra
    ldi $SQ_COL_ADDR_L
    mov marl, ra
    push marl
    push marh

    ldi #0xB0
    mov rb, ra
    mov rd, m
    ldi #8
    push ra
    call oled_clear_square
    mov rd, rb
    cmp zero
    jne fail

    pop marh
    pop marl
    mov rb, m
    ldi rd, #8
    add rb
    mov m, acc
    
    ; Page 0, column 0x70, data 0xFF.
    ldi #0xB0
    mov rb, ra
    mov rd, m
    ldi #8
    push ra
    call oled_draw_square
    mov rd, rb
    cmp zero
    jne fail

*wait_until_release:
    ldi $GPIO_BASE_H
    mov marh, ra
    ldi $BUTTON_GPIO_IN_L
    mov marl, ra
    mov rd, m
    cmp zero
    jne *wait_until_release

    call debounce_delay
    ldi $GPIO_BASE_H
    mov marh, ra
    ldi $BUTTON_GPIO_IN_L
    mov marl, ra
    mov rd, m
    cmp zero
    jne *wait_until_release


    jmp main_loop

debounce_delay:
    push lrl
    push lrh
    ldi rd, $BUTTON_DEBOUNCE
*debounce_loop:
    subi #1
    mov rd, acc
    jne *debounce_loop
    ret :stack

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
