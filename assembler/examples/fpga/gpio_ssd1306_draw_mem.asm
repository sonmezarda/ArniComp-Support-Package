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

equ SYS_LED_H            0x0C
equ SYS_LED_L            0x00
equ LED_OK               0x01
   
equ GPIO_BASE_H          0x08
equ BUTTON_GPIO_DIR_L    0x32
equ BUTTON_GPIO_IN_L     0x12
equ BUTTON_DEBOUNCE      0x80
   
equ SQ_COL_ADDR_H        0x00
equ SQ_COL_ADDR_L        0x20
   
equ PIXELS_ADDR_H        0x01  
equ PIXELS_ADDR_L        0x00  ;0x0100 -> 0x107F : pixels to draw (0x01:on 0x00: off)

equ CURRENT_PAGE_ADDR_H  0x00
equ CURRENT_PAGE_ADDR_L  0x01
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
    call draw_all_pixels

    jmp done

fail:
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    mov m, rb
    jmpa done

done:
    hlt
    hlt

draw_all_pixels:
*start:
    push lrl
    push lrh
    ldi $PIXELS_ADDR_H
    mov marh, ra
    mov marl, zero
    ldi #1
    mov m, ra
    inc #2
    mov m, ra
    inc #2
    inc #1
    mov m, ra

    mov marl, zero
    ldi rd, #0xB0

*draw_all_pages: ; rd = page ; mem setted
    ldi $CURRENT_PAGE_ADDR_H
    mov marh, ra
    ldi $CURRENT_PAGE_ADDR_L
    mov marl, ra
    ldi rd, #0xB7
    cmp m ; rd - ra 
    jeq *done
    
    ldi $PIXELS_ADDR_H
    mov marh, ra
    mov marl, zero
    clr rb

    *draw_page: ; rb = column pos ; mem setted
        ldi rd, #128
        cmp rb ; rd - rb
        jeq *draw_all_pages
        
        clr rd
        cmp m ; rd - m
        ldi rd, #0xB0
        jeq *draw_empty
        jmp *draw_fill

    *draw_empty: ; rd = page
        mov ra, rd
        mov rd, rb
        mov rb, ra
        push rd
        call draw_empty_pixel
        pop rb ; rb : colum pos
        ldi rd, #8
        add rb ; acc = rb + 8
        mov rb, acc
        inc #1
        jmp *draw_page

    *draw_fill:  ; rd = page
        mov ra, rd
        mov rd, rb
        mov rb, ra
        push rd
        call draw_filled_pixel
        pop rb
        ldi rd, #8
        add rb
        mov rb, acc
        inc #1
        jmp *draw_page

*done:
    ret :stack


draw_empty_pixel:
    ; rd : column select
    ; rb : page select
    push lrl
    push lrh
    push marl
    push marh
    ldi #8
    push ra
    call oled_clear_square
    pop marh
    pop marl
    ret :stack

draw_filled_pixel:
    ; rd : column select
    ; rb : page select
    push lrl
    push lrh
    push marl
    push marh
    ldi #8
    push ra
    call oled_draw_square
    pop marh
    pop marl
    ret :stack
/*
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


*/