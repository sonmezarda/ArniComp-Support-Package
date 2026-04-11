; Minimal SSD1306 clear-then-fill demo using software I2C on GPIO pins.
;
; Wiring:
; - gpio[0] / physical pin 25 -> SCL
; - gpio[1] / physical pin 26 -> SDA
;
; This demo initializes the OLED, clears all 8 pages to zero,
; then fills all 8 pages with 0xFF so the whole screen lights up.
;
; Visible LED result:
; - 0x01 -> success
; - 0x02 -> address NACK
; - 0x03 -> control-byte NACK
; - 0x04 -> command-byte NACK
; - 0x05 -> data-byte NACK

.import "../../lib/oled_soft_i2c.asm" oled_write_command, oled_init_basic, oled_set_page_column

equ GPIO_BASE_H       0x08
equ GPIO_IN1_L        0x11
equ GPIO_OUT0_L       0x20
equ GPIO_OUT1_L       0x21
equ GPIO_DIR0_L       0x30
equ GPIO_DIR1_L       0x31

equ SYS_LED_H         0x0C
equ SYS_LED_L         0x00
equ LED_OK            0x01
equ LED_FAIL_ADDR     0x02
equ LED_FAIL_CTRL     0x03
equ LED_FAIL_CMD      0x04
equ LED_FAIL_DATA     0x05

equ RAM_BASE_H        0x00
equ SCRATCH_BYTE_L    0x00
equ SCRATCH_COUNT_L   0x01

equ OLED_ADDR_W       0x78
equ OLED_CTRL_CMD     0x00
equ OLED_CTRL_DATA    0x40

equ SCL_DRIVE_LOW     0x01
equ SDA_DRIVE_LOW     0x01
equ DELAY_COUNT       1

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

    ; GPIO open-drain setup: keep OUT=0 and release both lines.
    ldi $GPIO_BASE_H
    mov marh, ra

    ldi $GPIO_OUT0_L
    mov marl, ra
    mov m, zero

    ldi $GPIO_OUT1_L
    mov marl, ra
    mov m, zero

    ldi $GPIO_DIR0_L
    mov marl, ra
    mov m, zero

    ldi $GPIO_DIR1_L
    mov marl, ra
    mov m, zero

    call delay_short
    nop

    ; Basic init from the shared soft-I2C OLED library.
    call oled_init_basic
    mov rd, rb
    cmp zero
    jne fail

    ; Clear all pages first.
    ldi #0xB0
    mov rb, ra
    call clear_page
    mov rd, rb
    cmp zero
    jne fail

    ldi #0xB1
    mov rb, ra
    call clear_page
    mov rd, rb
    cmp zero
    jne fail

    ldi #0xB2
    mov rb, ra
    call clear_page
    mov rd, rb
    cmp zero
    jne fail

    ldi #0xB3
    mov rb, ra
    call clear_page
    mov rd, rb
    cmp zero
    jne fail

    ldi #0xB4
    mov rb, ra
    call clear_page
    mov rd, rb
    cmp zero
    jne fail

    ldi #0xB5
    mov rb, ra
    call clear_page
    mov rd, rb
    cmp zero
    jne fail

    ldi #0xB6
    mov rb, ra
    call clear_page
    mov rd, rb
    cmp zero
    jne fail

    ldi #0xB7
    mov rb, ra
    call clear_page
    mov rd, rb
    cmp zero
    jne fail

    ; Then fill all pages with 0xFF.
    ldi #0xB0
    mov rb, ra
    call fill_page_ff
    mov rd, rb
    cmp zero
    jne fail

    ldi #0xB1
    mov rb, ra
    call fill_page_ff
    mov rd, rb
    cmp zero
    jne fail

    ldi #0xB2
    mov rb, ra
    call fill_page_ff
    mov rd, rb
    cmp zero
    jne fail

    ldi #0xB3
    mov rb, ra
    call fill_page_ff
    mov rd, rb
    cmp zero
    jne fail

    ldi #0xB4
    mov rb, ra
    call fill_page_ff
    mov rd, rb
    cmp zero
    jne fail

    ldi #0xB5
    mov rb, ra
    call fill_page_ff
    mov rd, rb
    cmp zero
    jne fail

    ldi #0xB6
    mov rb, ra
    call fill_page_ff
    mov rd, rb
    cmp zero
    jne fail

    ldi #0xB7
    mov rb, ra
    call fill_page_ff
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

write_command:
    ; In: RB = command byte
    ; Out: RB = 0 on success, LED code on failure
    push lrl
    push lrh

    ldi $RAM_BASE_H
    mov marh, ra
    ldi $SCRATCH_BYTE_L
    mov marl, ra
    mov m, rb

    call i2c_start

    ldi $OLED_ADDR_W
    mov rb, ra
    call send_byte
    call read_ack
    mov rd, rb
    cmp zero
    jne write_fail_addr

    ldi $OLED_CTRL_CMD
    mov rb, ra
    call send_byte
    call read_ack
    mov rd, rb
    cmp zero
    jne write_fail_ctrl

    ldi $RAM_BASE_H
    mov marh, ra
    ldi $SCRATCH_BYTE_L
    mov marl, ra
    mov rb, m

    call send_byte
    call read_ack
    mov rd, rb
    cmp zero
    jne write_fail_cmd

    call i2c_stop
    mov rb, zero
    ret :stack

begin_data_stream:
    ; Out: RB = 0 on success, LED code on failure
    push lrl
    push lrh

    call i2c_start

    ldi $OLED_ADDR_W
    mov rb, ra
    call send_byte
    call read_ack
    mov rd, rb
    cmp zero
    jne write_fail_addr

    ldi $OLED_CTRL_DATA
    mov rb, ra
    call send_byte
    call read_ack
    mov rd, rb
    cmp zero
    jne write_fail_ctrl

    mov rb, zero
    ret :stack

    ; Keep stream_data_byte target low-byte away from the 0x1F boundary
    ; so CALL size estimation stays stable across passes.
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop

stream_data_byte:
    ; In: RB = data byte
    ; Out: RB = 0 on success, LED code on failure
    push lrl
    push lrh

    call send_byte
    call read_ack
    mov rd, rb
    cmp zero
    jne write_fail_data

    mov rb, zero
    ret :stack

clear_page:
    ; In: RB = page-select command 0xB0..0xB7
    ; Out: RB = 0 on success, LED code on failure
    push lrl
    push lrh

    mov rd, zero
    call oled_set_page_column
    mov rd, rb
    cmp zero
    jne page_fail

    call begin_data_stream
    mov rd, rb
    cmp zero
    jne page_fail

    ldi $RAM_BASE_H
    mov marh, ra
    ldi $SCRATCH_COUNT_L
    mov marl, ra
    ldi #0x80
    mov m, ra

clear_zero_loop:
    mov rb, zero
    call stream_data_byte
    mov rd, rb
    cmp zero
    jne page_fail

    ldi $RAM_BASE_H
    mov marh, ra
    ldi $SCRATCH_COUNT_L
    mov marl, ra
    mov rd, m
    subi #1
    mov rd, acc
    mov m, rd
    jne clear_zero_loop

    call i2c_stop
    mov rb, zero
    ret :stack

fill_page_ff:
    ; In: RB = page-select command 0xB0..0xB7
    ; Out: RB = 0 on success, LED code on failure
    push lrl
    push lrh

    mov rd, zero
    call oled_set_page_column
    mov rd, rb
    cmp zero
    jne page_fail

    call begin_data_stream
    mov rd, rb
    cmp zero
    jne page_fail

    ldi $RAM_BASE_H
    mov marh, ra
    ldi $SCRATCH_COUNT_L
    mov marl, ra
    ldi #0x80
    mov m, ra

fill_ff_loop:
    ldi #0xFF
    mov rb, ra
    call stream_data_byte
    mov rd, rb
    cmp zero
    jne page_fail

    ldi $RAM_BASE_H
    mov marh, ra
    ldi $SCRATCH_COUNT_L
    mov marl, ra
    mov rd, m
    subi #1
    mov rd, acc
    mov m, rd
    jne fill_ff_loop

    call i2c_stop
    mov rb, zero
    ret :stack

page_fail:
    call i2c_stop
    ret :stack

write_fail_addr:
    call i2c_stop
    ldi $LED_FAIL_ADDR
    mov rb, ra
    ret :stack

write_fail_ctrl:
    call i2c_stop
    ldi $LED_FAIL_CTRL
    mov rb, ra
    ret :stack

write_fail_cmd:
    call i2c_stop
    ldi $LED_FAIL_CMD
    mov rb, ra
    ret :stack

write_fail_data:
    call i2c_stop
    ldi $LED_FAIL_DATA
    mov rb, ra
    ret :stack

i2c_start:
    push lrl
    push lrh

    ldi $GPIO_BASE_H
    mov marh, ra
    ldi $GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    ldi $GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call delay_short

    ldi $GPIO_DIR1_L
    mov marl, ra
    ldi $SDA_DRIVE_LOW
    mov m, ra
    call delay_short

    ldi $GPIO_DIR0_L
    mov marl, ra
    ldi $SCL_DRIVE_LOW
    mov m, ra
    call delay_short
    ret :stack

i2c_stop:
    push lrl
    push lrh

    ldi $GPIO_BASE_H
    mov marh, ra

    ldi $GPIO_DIR1_L
    mov marl, ra
    ldi $SDA_DRIVE_LOW
    mov m, ra
    call delay_short

    ldi $GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    call delay_short

    ldi $GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call delay_short
    ret :stack

read_ack:
    push lrl
    push lrh

    ldi $GPIO_BASE_H
    mov marh, ra
    ldi $GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call delay_short

    ldi $GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    call delay_short
    call delay_short

    ldi $GPIO_IN1_L
    mov marl, ra
    mov rd, m
    mov rb, rd

    ldi $GPIO_DIR0_L
    mov marl, ra
    ldi $SCL_DRIVE_LOW
    mov m, ra
    call delay_short
    ret :stack

send_byte:
    push lrl
    push lrh

    ; Bit 7
    mov rd, rb
    ldi #0x80
    and ra
    mov rd, acc
    cmp zero
    jeq send_b7_zero
    call send_bit_one
    jmp send_b6
send_b7_zero:
    call send_bit_zero

send_b6:
    mov rd, rb
    ldi #0x40
    and ra
    mov rd, acc
    cmp zero
    jeq send_b6_zero
    call send_bit_one
    jmp send_b5
send_b6_zero:
    call send_bit_zero

send_b5:
    mov rd, rb
    ldi #0x20
    and ra
    mov rd, acc
    cmp zero
    jeq send_b5_zero
    call send_bit_one
    jmp send_b4
send_b5_zero:
    call send_bit_zero

send_b4:
    mov rd, rb
    ldi #0x10
    and ra
    mov rd, acc
    cmp zero
    jeq send_b4_zero
    call send_bit_one
    jmp send_b3
send_b4_zero:
    call send_bit_zero

send_b3:
    mov rd, rb
    ldi #0x08
    and ra
    mov rd, acc
    cmp zero
    jeq send_b3_zero
    call send_bit_one
    jmp send_b2
send_b3_zero:
    call send_bit_zero

send_b2:
    mov rd, rb
    ldi #0x04
    and ra
    mov rd, acc
    cmp zero
    jeq send_b2_zero
    call send_bit_one
    jmp send_b1
send_b2_zero:
    call send_bit_zero

send_b1:
    mov rd, rb
    ldi #0x02
    and ra
    mov rd, acc
    cmp zero
    jeq send_b1_zero
    call send_bit_one
    jmp send_b0

    ; Keep both send_b1_zero and send_bit_zero target low-bytes on a stable
    ; side of the short-LDI boundary for macro sizing.
    nop
    nop
    nop
    nop
    nop

send_b1_zero:
    call send_bit_zero

send_b0:
    mov rd, rb
    ldi #0x01
    and ra
    mov rd, acc
    cmp zero
    jeq send_b0_zero
    call send_bit_one
    ret :stack
send_b0_zero:
    call send_bit_zero
    ret :stack

send_bit_zero:
    push lrl
    push lrh

    ldi $GPIO_BASE_H
    mov marh, ra
    ldi $GPIO_DIR1_L
    mov marl, ra
    ldi $SDA_DRIVE_LOW
    mov m, ra
    call pulse_scl
    ret :stack

send_bit_one:
    push lrl
    push lrh

    ldi $GPIO_BASE_H
    mov marh, ra
    ldi $GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call pulse_scl
    ret :stack

pulse_scl:
    push lrl
    push lrh

    call delay_short
    ldi $GPIO_BASE_H
    mov marh, ra
    ldi $GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    call delay_short
    call delay_short
    ldi $GPIO_DIR0_L
    mov marl, ra
    ldi $SCL_DRIVE_LOW
    mov m, ra
    call delay_short
    ret :stack

delay_short:
    ldi rd, $DELAY_COUNT

delay_loop:
    subi #1
    mov rd, acc
    jne delay_loop
    ret

done:
    jmpa done
