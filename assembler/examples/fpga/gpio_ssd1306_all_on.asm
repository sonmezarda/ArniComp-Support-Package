; Minimal SSD1306 bring-up using software I2C on GPIO pins.
;
; Wiring:
; - gpio[0] / physical pin 25 -> SCL
; - gpio[1] / physical pin 26 -> SDA
;
; Open-drain emulation:
; - GPIO_OUT bits stay at 0
; - DIR=1 drives low
; - DIR=0 releases the line high
;
; Success path:
; - OLED should light up fully after A5 + AF
; - SYS LED = 0x01
;
; Failure path:
; - SYS LED = 0x02 on address NACK
; - SYS LED = 0x03 on control-byte NACK
; - SYS LED = 0x04 on command NACK

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

equ RAM_BASE_H        0x00
equ SCRATCH_CMD_L     0x00

equ OLED_ADDR_W       0x78
equ OLED_CTRL_CMD     0x00

equ SCL_DRIVE_LOW     0x01
equ SDA_DRIVE_LOW     0x01
equ DELAY_COUNT       16

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

    ; Minimal SSD1306 init subset, then force all pixels on.
    ldi #0xAE
    mov rb, ra
    call write_command
    mov rd, rb
    cmp zero
    jne fail

    ldi #0x8D
    mov rb, ra
    call write_command
    mov rd, rb
    cmp zero
    jne fail

    ldi #0x14
    mov rb, ra
    call write_command
    mov rd, rb
    cmp zero
    jne fail

    ldi #0xAF
    mov rb, ra
    call write_command
    mov rd, rb
    cmp zero
    jne fail

    ldi #0xA5
    mov rb, ra
    call write_command
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
    ; In:  RB = command byte
    ; Out: RB = 0 on success, LED code on failure
    push lrl
    push lrh

    ; Save command byte in scratch RAM.
    ldi $RAM_BASE_H
    mov marh, ra
    ldi $SCRATCH_CMD_L
    mov marl, ra
    mov m, rb

    call i2c_start

    ; Send slave address.
    ldi $OLED_ADDR_W
    mov rb, ra
    call send_byte
    call read_ack
    mov rd, rb
    cmp zero
    jne write_command_fail_addr

    ; Send control byte for command stream.
    ldi $OLED_CTRL_CMD
    mov rb, ra
    call send_byte
    call read_ack
    mov rd, rb
    cmp zero
    jne write_command_fail_ctrl

    ; Reload and send the command byte.
    ldi $RAM_BASE_H
    mov marh, ra
    ldi $SCRATCH_CMD_L
    mov marl, ra
    mov rb, m

    call send_byte
    call read_ack
    mov rd, rb
    cmp zero
    jne write_command_fail_cmd

    call i2c_stop
    mov rb, zero
    ret :stack

write_command_fail_addr:
    call i2c_stop
    ldi $LED_FAIL_ADDR
    mov rb, ra
    ret :stack

write_command_fail_ctrl:
    call i2c_stop
    ldi $LED_FAIL_CTRL
    mov rb, ra
    ret :stack

write_command_fail_cmd:
    call i2c_stop
    ldi $LED_FAIL_CMD
    mov rb, ra
    ret :stack

i2c_start:
    push lrl
    push lrh

    ; Release both lines high.
    ldi $GPIO_BASE_H
    mov marh, ra
    ldi $GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    ldi $GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call delay_short

    ; SDA low while SCL high.
    ldi $GPIO_DIR1_L
    mov marl, ra
    ldi $SDA_DRIVE_LOW
    mov m, ra
    call delay_short

    ; Pull SCL low for data phase.
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

    ; Ensure SDA low while SCL low.
    ldi $GPIO_DIR1_L
    mov marl, ra
    ldi $SDA_DRIVE_LOW
    mov m, ra
    call delay_short

    ; Release SCL high.
    ldi $GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    call delay_short

    ; Release SDA high.
    ldi $GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call delay_short
    ret :stack

read_ack:
    ; Out: RB = sampled SDA value, 0 means ACK
    push lrl
    push lrh

    ldi $GPIO_BASE_H
    mov marh, ra
    ldi $GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call delay_short

    ; Clock ACK bit high.
    ldi $GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    call delay_short
    call delay_short

    ; Sample SDA into RB.
    ldi $GPIO_IN1_L
    mov marl, ra
    mov rd, m
    mov rb, rd

    ; Finish clock.
    ldi $GPIO_DIR0_L
    mov marl, ra
    ldi $SCL_DRIVE_LOW
    mov m, ra
    call delay_short
    ret :stack

send_byte:
    ; In: RB = byte to send
    ; Sends MSB first.
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
