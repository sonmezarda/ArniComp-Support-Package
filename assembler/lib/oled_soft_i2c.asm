.include "../includes/function_abi.asm"

equ OLED_GPIO_BASE_H    0x08
equ OLED_GPIO_IN1_L     0x11
equ OLED_GPIO_OUT0_L    0x20
equ OLED_GPIO_OUT1_L    0x21
equ OLED_GPIO_DIR0_L    0x30
equ OLED_GPIO_DIR1_L    0x31

equ OLED_ADDR_W         0x78
equ OLED_CTRL_CMD       0x00
equ OLED_CTRL_DATA      0x40
equ OLED_ERR_ADDR       0x02
equ OLED_ERR_CTRL       0x03
equ OLED_ERR_CMD        0x04
equ OLED_ERR_DATA       0x05

equ OLED_SCL_DRIVE_LOW  0x01
equ OLED_SDA_DRIVE_LOW  0x01
equ OLED_DELAY_COUNT    16

.export oled_gpio_bus_init
.func
oled_gpio_bus_init:
    ; oled_gpio_bus_init
    ; in :
    ;   none
    ; out:
    ;   RB = 0 if no error
    ; clobbers:
    ;   RA, RD, ACC, flags, MARL, MARH
    ; scratch:
    ;   none

    ldi $OLED_GPIO_BASE_H
    mov marh, ra

    ; OUT stays 0, DIR=1 drives low, DIR=0 releases high.
    ldi $OLED_GPIO_OUT0_L
    mov marl, ra
    mov m, zero

    ldi $OLED_GPIO_OUT1_L
    mov marl, ra
    mov m, zero

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    mov m, zero

    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    mov m, zero

    mov rb, zero
    ret
.endfunc

.export oled_write_command
.func
oled_write_command:
    ; oled_write_command
    ; in :
    ;   RB = command byte
    ; out:
    ;   RB = 0 on success
    ;   RB = 0x02 address ACK failed
    ;   RB = 0x03 control ACK failed
    ;   RB = 0x04 command ACK failed
    ; import note:
    ;   self-contained

    push lrl
    push lrh

    ldi $F_TMP_BASE_H
    mov marh, ra
    ldi $F_T0_L
    mov marl, ra
    mov m, rb

    call @*i2c_start

    ldi $OLED_ADDR_W
    mov rb, ra
    call @*send_byte
    call @*read_ack
    mov rd, rb
    cmp zero
    jne @*fail_addr

    ldi $OLED_CTRL_CMD
    mov rb, ra
    call @*send_byte
    call @*read_ack
    mov rd, rb
    cmp zero
    jne @*fail_ctrl

    ldi $F_TMP_BASE_H
    mov marh, ra
    ldi $F_T0_L
    mov marl, ra
    mov rb, m
    call @*send_byte
    call @*read_ack
    mov rd, rb
    cmp zero
    jne @*fail_cmd

    call @*i2c_stop
    mov rb, zero
    ret :stack

*fail_addr:
    call @*i2c_stop
    ldi $OLED_ERR_ADDR
    mov rb, ra
    ret :stack

*fail_ctrl:
    call @*i2c_stop
    ldi $OLED_ERR_CTRL
    mov rb, ra
    ret :stack

*fail_cmd:
    call @*i2c_stop
    ldi $OLED_ERR_CMD
    mov rb, ra
    ret :stack

*i2c_start:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call @*delay_short

    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    ldi $OLED_SDA_DRIVE_LOW
    mov m, ra
    call @*delay_short

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    ldi $OLED_SCL_DRIVE_LOW
    mov m, ra
    call @*delay_short
    ret :stack

*i2c_stop:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra

    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    ldi $OLED_SDA_DRIVE_LOW
    mov m, ra
    call @*delay_short

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    call @*delay_short

    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call @*delay_short
    ret :stack

*read_ack:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call @*delay_short

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    call @*delay_short
    call @*delay_short

    ldi $OLED_GPIO_IN1_L
    mov marl, ra
    mov rd, m
    mov rb, rd

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    ldi $OLED_SCL_DRIVE_LOW
    mov m, ra
    call @*delay_short
    ret :stack

*send_byte:
    push lrl
    push lrh

    mov rd, rb
    ldi #0x80
    and ra
    mov rd, acc
    cmp zero
    jeq @*b7_zero
    call @*send_bit_one
    jmp @*b6
*b7_zero:
    call @*send_bit_zero

*b6:
    mov rd, rb
    ldi #0x40
    and ra
    mov rd, acc
    cmp zero
    jeq @*b6_zero
    call @*send_bit_one
    jmp @*b5
*b6_zero:
    call @*send_bit_zero

*b5:
    mov rd, rb
    ldi #0x20
    and ra
    mov rd, acc
    cmp zero
    jeq @*b5_zero
    call @*send_bit_one
    jmp @*b4
*b5_zero:
    call @*send_bit_zero

*b4:
    mov rd, rb
    ldi #0x10
    and ra
    mov rd, acc
    cmp zero
    jeq @*b4_zero
    call @*send_bit_one
    jmp @*b3
*b4_zero:
    call @*send_bit_zero

*b3:
    mov rd, rb
    ldi #0x08
    and ra
    mov rd, acc
    cmp zero
    jeq @*b3_zero
    call @*send_bit_one
    jmp @*b2
*b3_zero:
    call @*send_bit_zero

*b2:
    mov rd, rb
    ldi #0x04
    and ra
    mov rd, acc
    cmp zero
    jeq @*b2_zero
    call @*send_bit_one
    jmp @*b1
*b2_zero:
    call @*send_bit_zero

*b1:
    mov rd, rb
    ldi #0x02
    and ra
    mov rd, acc
    cmp zero
    jeq @*b1_zero
    call @*send_bit_one
    jmp @*b0
    nop
    nop
    nop
    nop
    nop
*b1_zero:
    call @*send_bit_zero

*b0:
    mov rd, rb
    ldi #0x01
    and ra
    mov rd, acc
    cmp zero
    jeq @*b0_zero
    call @*send_bit_one
    ret :stack
*b0_zero:
    call @*send_bit_zero
    ret :stack

*send_bit_zero:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    ldi $OLED_SDA_DRIVE_LOW
    mov m, ra
    call @*pulse_scl
    ret :stack

*send_bit_one:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call @*pulse_scl
    ret :stack

*pulse_scl:
    push lrl
    push lrh

    call @*delay_short
    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    call @*delay_short
    call @*delay_short
    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    ldi $OLED_SCL_DRIVE_LOW
    mov m, ra
    call @*delay_short
    ret :stack

*delay_short:
    ldi rd, $OLED_DELAY_COUNT
*delay_loop:
    subi #1
    mov rd, acc
    jne @*delay_loop
    ret
.endfunc

.export oled_begin_data_stream
.func
oled_begin_data_stream:
    ; oled_begin_data_stream
    ; out:
    ;   RB = 0 on success
    ;   RB = 0x02 address ACK failed
    ;   RB = 0x03 control ACK failed

    push lrl
    push lrh

    call @*i2c_start

    ldi $OLED_ADDR_W
    mov rb, ra
    call @*send_byte
    call @*read_ack
    mov rd, rb
    cmp zero
    jne @*fail_addr

    ldi $OLED_CTRL_DATA
    mov rb, ra
    call @*send_byte
    call @*read_ack
    mov rd, rb
    cmp zero
    jne @*fail_ctrl

    mov rb, zero
    ret :stack

*fail_addr:
    call @*i2c_stop
    ldi $OLED_ERR_ADDR
    mov rb, ra
    ret :stack

*fail_ctrl:
    call @*i2c_stop
    ldi $OLED_ERR_CTRL
    mov rb, ra
    ret :stack

*i2c_start:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call @*delay_short

    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    ldi $OLED_SDA_DRIVE_LOW
    mov m, ra
    call @*delay_short

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    ldi $OLED_SCL_DRIVE_LOW
    mov m, ra
    call @*delay_short
    ret :stack

*i2c_stop:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra

    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    ldi $OLED_SDA_DRIVE_LOW
    mov m, ra
    call @*delay_short

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    call @*delay_short

    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call @*delay_short
    ret :stack

*read_ack:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call @*delay_short

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    call @*delay_short
    call @*delay_short

    ldi $OLED_GPIO_IN1_L
    mov marl, ra
    mov rd, m
    mov rb, rd

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    ldi $OLED_SCL_DRIVE_LOW
    mov m, ra
    call @*delay_short
    ret :stack

*send_byte:
    push lrl
    push lrh

    mov rd, rb
    ldi #0x80
    and ra
    mov rd, acc
    cmp zero
    jeq @*b7_zero
    call @*send_bit_one
    jmp @*b6
*b7_zero:
    call @*send_bit_zero

*b6:
    mov rd, rb
    ldi #0x40
    and ra
    mov rd, acc
    cmp zero
    jeq @*b6_zero
    call @*send_bit_one
    jmp @*b5
*b6_zero:
    call @*send_bit_zero

*b5:
    mov rd, rb
    ldi #0x20
    and ra
    mov rd, acc
    cmp zero
    jeq @*b5_zero
    call @*send_bit_one
    jmp @*b4
*b5_zero:
    call @*send_bit_zero

*b4:
    mov rd, rb
    ldi #0x10
    and ra
    mov rd, acc
    cmp zero
    jeq @*b4_zero
    call @*send_bit_one
    jmp @*b3
*b4_zero:
    call @*send_bit_zero

*b3:
    mov rd, rb
    ldi #0x08
    and ra
    mov rd, acc
    cmp zero
    jeq @*b3_zero
    call @*send_bit_one
    jmp @*b2
*b3_zero:
    call @*send_bit_zero

*b2:
    mov rd, rb
    ldi #0x04
    and ra
    mov rd, acc
    cmp zero
    jeq @*b2_zero
    call @*send_bit_one
    jmp @*b1
*b2_zero:
    call @*send_bit_zero

*b1:
    mov rd, rb
    ldi #0x02
    and ra
    mov rd, acc
    cmp zero
    jeq @*b1_zero
    call @*send_bit_one
    jmp @*b0
    nop
    nop
    nop
    nop
    nop
*b1_zero:
    call @*send_bit_zero

*b0:
    mov rd, rb
    ldi #0x01
    and ra
    mov rd, acc
    cmp zero
    jeq @*b0_zero
    call @*send_bit_one
    ret :stack
*b0_zero:
    call @*send_bit_zero
    ret :stack

*send_bit_zero:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    ldi $OLED_SDA_DRIVE_LOW
    mov m, ra
    call @*pulse_scl
    ret :stack

*send_bit_one:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call @*pulse_scl
    ret :stack

*pulse_scl:
    push lrl
    push lrh

    call @*delay_short
    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    call @*delay_short
    call @*delay_short
    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    ldi $OLED_SCL_DRIVE_LOW
    mov m, ra
    call @*delay_short
    ret :stack

*delay_short:
    ldi rd, $OLED_DELAY_COUNT
*delay_loop:
    subi #1
    mov rd, acc
    jne @*delay_loop
    ret
.endfunc

.export oled_stream_data_byte
.func
oled_stream_data_byte:
    ; oled_stream_data_byte
    ; in :
    ;   RB = data byte
    ; out:
    ;   RB = 0 on success
    ;   RB = 0x05 data ACK failed

    push lrl
    push lrh

    call @*send_byte
    call @*read_ack
    mov rd, rb
    cmp zero
    jne @*fail_data

    mov rb, zero
    ret :stack

*fail_data:
    call @*i2c_stop
    ldi $OLED_ERR_DATA
    mov rb, ra
    ret :stack

*i2c_stop:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra

    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    ldi $OLED_SDA_DRIVE_LOW
    mov m, ra
    call @*delay_short

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    call @*delay_short

    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call @*delay_short
    ret :stack

*read_ack:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call @*delay_short

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    call @*delay_short
    call @*delay_short

    ldi $OLED_GPIO_IN1_L
    mov marl, ra
    mov rd, m
    mov rb, rd

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    ldi $OLED_SCL_DRIVE_LOW
    mov m, ra
    call @*delay_short
    ret :stack

*send_byte:
    push lrl
    push lrh

    mov rd, rb
    ldi #0x80
    and ra
    mov rd, acc
    cmp zero
    jeq @*b7_zero
    call @*send_bit_one
    jmp @*b6
*b7_zero:
    call @*send_bit_zero

*b6:
    mov rd, rb
    ldi #0x40
    and ra
    mov rd, acc
    cmp zero
    jeq @*b6_zero
    call @*send_bit_one
    jmp @*b5
*b6_zero:
    call @*send_bit_zero

*b5:
    mov rd, rb
    ldi #0x20
    and ra
    mov rd, acc
    cmp zero
    jeq @*b5_zero
    call @*send_bit_one
    jmp @*b4
*b5_zero:
    call @*send_bit_zero

*b4:
    mov rd, rb
    ldi #0x10
    and ra
    mov rd, acc
    cmp zero
    jeq @*b4_zero
    call @*send_bit_one
    jmp @*b3
*b4_zero:
    call @*send_bit_zero

*b3:
    mov rd, rb
    ldi #0x08
    and ra
    mov rd, acc
    cmp zero
    jeq @*b3_zero
    call @*send_bit_one
    jmp @*b2
*b3_zero:
    call @*send_bit_zero

*b2:
    mov rd, rb
    ldi #0x04
    and ra
    mov rd, acc
    cmp zero
    jeq @*b2_zero
    call @*send_bit_one
    jmp @*b1
*b2_zero:
    call @*send_bit_zero

*b1:
    mov rd, rb
    ldi #0x02
    and ra
    mov rd, acc
    cmp zero
    jeq @*b1_zero
    call @*send_bit_one
    jmp @*b0
    nop
    nop
    nop
    nop
    nop
*b1_zero:
    call @*send_bit_zero

*b0:
    mov rd, rb
    ldi #0x01
    and ra
    mov rd, acc
    cmp zero
    jeq @*b0_zero
    call @*send_bit_one
    ret :stack
*b0_zero:
    call @*send_bit_zero
    ret :stack

*send_bit_zero:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    ldi $OLED_SDA_DRIVE_LOW
    mov m, ra
    call @*pulse_scl
    ret :stack

*send_bit_one:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call @*pulse_scl
    ret :stack

*pulse_scl:
    push lrl
    push lrh

    call @*delay_short
    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    call @*delay_short
    call @*delay_short
    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    ldi $OLED_SCL_DRIVE_LOW
    mov m, ra
    call @*delay_short
    ret :stack

*delay_short:
    ldi rd, $OLED_DELAY_COUNT
*delay_loop:
    subi #1
    mov rd, acc
    jne @*delay_loop
    ret
.endfunc

.export oled_end_stream
.func
oled_end_stream:
    ; oled_end_stream
    ; out:
    ;   RB = 0

    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra

    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    ldi $OLED_SDA_DRIVE_LOW
    mov m, ra
    call @*delay_short

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    call @*delay_short

    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call @*delay_short

    mov rb, zero
    ret :stack

*delay_short:
    ldi rd, $OLED_DELAY_COUNT
*delay_loop:
    subi #1
    mov rd, acc
    jne @*delay_loop
    ret
.endfunc

.export oled_init_basic
.func
oled_init_basic:
    ; oled_init_basic
    ; out:
    ;   RB = 0 on success
    ;   RB = 0x02 address ACK failed
    ;   RB = 0x03 control ACK failed
    ;   RB = 0x04 command ACK failed
    ; import note:
    ;   import oled_write_command too.

    push lrl
    push lrh

    ldi #0xAE
    mov rb, ra
    call oled_write_command
    mov rd, rb
    cmp zero
    jne @*fail

    ldi #0x8D
    mov rb, ra
    call oled_write_command
    mov rd, rb
    cmp zero
    jne @*fail

    ldi #0x14
    mov rb, ra
    call oled_write_command
    mov rd, rb
    cmp zero
    jne @*fail

    ldi #0x20
    mov rb, ra
    call oled_write_command
    mov rd, rb
    cmp zero
    jne @*fail

    ldi #0x02
    mov rb, ra
    call oled_write_command
    mov rd, rb
    cmp zero
    jne @*fail

    ldi #0xA4
    mov rb, ra
    call oled_write_command
    mov rd, rb
    cmp zero
    jne @*fail

    ldi #0xA6
    mov rb, ra
    call oled_write_command
    mov rd, rb
    cmp zero
    jne @*fail

    ldi #0xAF
    mov rb, ra
    call oled_write_command
    ret :stack

*fail:
    ret :stack
.endfunc

.export oled_set_page_column_direct
.func
oled_set_page_column_direct:
    ; oled_set_page_column_direct
    ; Sends the proven direct command sequence:
    ;   page command
    ;   lower-column command 0x00..0x0F
    ;   upper-column command 0x10..0x17
    ; in :
    ;   RB = page command (0xB0..0xB7)
    ;   RD = column address (0x00..0x7F)
    ; out:
    ;   RB = 0 on success
    ;   RB = 0x02 address ACK failed
    ;   RB = 0x03 control ACK failed
    ;   RB = 0x04 command ACK failed
    ; import note:
    ;   import oled_write_command too.
    ; scratch:
    ;   F_T4_L = saved page command
    ;   F_T5_L = saved column address
    ;   F_T6_L = mask / upper-column command scratch

    push lrl
    push lrh

    ldi $F_TMP_BASE_H
    mov marh, ra
    ldi $F_T4_L
    mov marl, ra
    mov m, rb

    ldi $F_T5_L
    mov marl, ra
    mov m, rd

    ; Send page command.
    ldi $F_T4_L
    mov marl, ra
    mov rb, m
    call oled_write_command
    mov rd, rb
    cmp zero
    jne @*fail

    ; oled_write_command does not preserve MARH; restore scratch page.
    ldi $F_TMP_BASE_H
    mov marh, ra

    ; Send lower column nibble command (0x00..0x0F).
    ldi $F_T6_L
    mov marl, ra
    ldi #0x0F
    mov m, ra

    ldi $F_T5_L
    mov marl, ra
    mov rd, m
    ldi $F_T6_L
    mov marl, ra
    and m
    mov rb, acc
    call oled_write_command
    mov rd, rb
    cmp zero
    jne @*fail

    ; oled_write_command does not preserve MARH; restore scratch page.
    ldi $F_TMP_BASE_H
    mov marh, ra

    ; Build upper column command (0x10..0x17).
    ldi $F_T6_L
    mov marl, ra
    ldi #0x10
    mov m, ra

    ldi $F_T5_L
    mov marl, ra
    mov rd, m
    ldi #0x10
    and ra
    mov rd, acc
    cmp zero
    jeq @*skip_add1
    ldi $F_T6_L
    mov marl, ra
    mov rd, m
    addi #1
    mov m, acc
*skip_add1:

    ldi $F_T5_L
    mov marl, ra
    mov rd, m
    ldi #0x20
    and ra
    mov rd, acc
    cmp zero
    jeq @*skip_add2
    ldi $F_T6_L
    mov marl, ra
    mov rd, m
    addi #2
    mov m, acc
*skip_add2:

    ldi $F_T5_L
    mov marl, ra
    mov rd, m
    ldi #0x40
    and ra
    mov rd, acc
    cmp zero
    jeq @*send_upper
    ldi $F_T6_L
    mov marl, ra
    mov rd, m
    addi #4
    mov m, acc

*send_upper:
    ldi $F_T6_L
    mov marl, ra
    mov rb, m
    call oled_write_command
    ret :stack

*fail:
    ret :stack
.endfunc

.export oled_set_page_column
.func
oled_set_page_column:
    ; Backward-compatible alias for the direct page/column helper.
    call oled_set_page_column_direct
    ret :stack
.endfunc

.export oled_fill_screen
.func
oled_fill_screen:
    ; oled_fill_screen
    ; in :
    ;   RB = fill byte
    ; out:
    ;   RB = 0 on success
    ;   non-zero on first write/data error
    ; import note:
    ;   import oled_write_command, oled_begin_data_stream,
    ;   oled_stream_data_byte, oled_end_stream too.

    push lrl
    push lrh

    ldi $F_TMP_BASE_H
    mov marh, ra
    ldi $F_T4_L
    mov marl, ra
    mov m, rb

    ldi $F_T5_L
    mov marl, ra
    ldi #0xB0
    mov m, ra

*page_loop:
    ldi $F_TMP_BASE_H
    mov marh, ra
    ldi $F_T5_L
    mov marl, ra
    mov rb, m
    call oled_write_command
    mov rd, rb
    cmp zero
    jne @*fail

    ldi #0xFF
    mov rb, ra
    call oled_write_command
    mov rd, rb
    cmp zero
    jne @*fail

    ldi #0x10
    mov rb, ra
    call oled_write_command
    mov rd, rb
    cmp zero
    jne @*fail

    call oled_begin_data_stream
    mov rd, rb
    cmp zero
    jne @*fail

    ldi $F_TMP_BASE_H
    mov marh, ra
    ldi $F_T6_L
    mov marl, ra
    ldi #0x80
    mov m, ra

*data_loop:
    ldi $F_TMP_BASE_H
    mov marh, ra
    ldi $F_T4_L
    mov marl, ra
    mov rb, m
    call oled_stream_data_byte
    mov rd, rb
    cmp zero
    jne @*fail

    ldi $F_TMP_BASE_H
    mov marh, ra
    ldi $F_T6_L
    mov marl, ra
    mov rd, m
    subi #1
    mov rd, acc
    mov m, rd
    jne @*data_loop

    call oled_end_stream

    ldi $F_TMP_BASE_H
    mov marh, ra
    ldi $F_T5_L
    mov marl, ra
    mov rd, m
    addi #1
    mov rd, acc
    mov m, rd

    ldi #0xB8
    cmp ra
    jne @*page_loop

    mov rb, zero
    ret :stack

*fail:
    ret :stack
.endfunc

.export oled_clear_screen
.func
oled_clear_screen:
    ; oled_clear_screen
    ; out:
    ;   RB = 0 on success
    ;   non-zero on first write/data error

    push lrl
    push lrh

    mov rb, zero
    call oled_fill_screen
    ret :stack
.endfunc

.export oled_write_stack_noack
.func
oled_write_stack_noack:
    ; oled_write_stack_noack
    ; in :
    ;   RB = byte count
    ;   RD = control byte (0x00 command, 0x40 data)
    ;   stack top = first byte to send
    ; out:
    ;   RB = 0
    ; clobbers:
    ;   RA, RD, ACC, flags, MARL, MARH, PRL, PRH
    ; scratch:
    ;   F_T0_L = remaining count
    ;   F_T1_L = control byte
    ;   F_T2_L = saved return low
    ;   F_T3_L = saved return high
    ;
    ; caller note:
    ;   because bytes are popped from the stack, push them in reverse order.
    ;   example to send AE 8D 14:
    ;     pushi #0x14
    ;     pushi #0x8D
    ;     pushi #0xAE
    ;     ldi #3
    ;     mov rb, ra
    ;     ldi $OLED_CTRL_CMD
    ;     mov rd, ra
    ;     call oled_write_stack_noack

    ; Save our return address plus count/control into shared scratch so the
    ; payload bytes at the top of the caller stack can be popped safely.
    ldi $F_TMP_BASE_H
    mov marh, ra
    ldi $F_T0_L
    mov marl, ra
    mov m, rb
    ldi $F_T1_L
    mov marl, ra
    mov m, rd
    ldi $F_T2_L
    mov marl, ra
    mov m, lrl
    ldi $F_T3_L
    mov marl, ra
    mov m, lrh

    call @*i2c_start

    ; Slave address + write
    ldi $OLED_ADDR_W
    mov rb, ra
    call @*send_byte
    call @*ack_clock_only

    ; Control byte
    ldi $F_TMP_BASE_H
    mov marh, ra
    ldi $F_T1_L
    mov marl, ra
    mov rb, m
    call @*send_byte
    call @*ack_clock_only

*loop:
    ldi $F_TMP_BASE_H
    mov marh, ra
    ldi $F_T0_L
    mov marl, ra
    mov rd, m
    cmp zero
    jeq @*done

    pop rb
    call @*send_byte
    call @*ack_clock_only

    ldi $F_TMP_BASE_H
    mov marh, ra
    ldi $F_T0_L
    mov marl, ra
    mov rd, m
    subi #1
    mov rd, acc
    mov m, rd
    jmpa @*loop

*done:
    call @*i2c_stop
    mov rb, zero
    ldi $F_TMP_BASE_H
    mov marh, ra
    ldi $F_T2_L
    mov marl, ra
    mov ra, m
    mov prl, ra
    ldi $F_T3_L
    mov marl, ra
    mov ra, m
    mov prh, ra
    jmp

*i2c_start:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call @*delay_short

    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    ldi $OLED_SDA_DRIVE_LOW
    mov m, ra
    call @*delay_short

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    ldi $OLED_SCL_DRIVE_LOW
    mov m, ra
    call @*delay_short
    ret :stack

*i2c_stop:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra

    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    ldi $OLED_SDA_DRIVE_LOW
    mov m, ra
    call @*delay_short

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    call @*delay_short

    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call @*delay_short
    ret :stack

*ack_clock_only:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra

    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call @*delay_short

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    call @*delay_short
    call @*delay_short

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    ldi $OLED_SCL_DRIVE_LOW
    mov m, ra
    call @*delay_short
    ret :stack

*send_byte:
    ; In: RB = byte to send, MSB first.
    push lrl
    push lrh

    mov rd, rb
    ldi #0x80
    and ra
    mov rd, acc
    cmp zero
    jeq @*b7_zero
    call @*send_bit_one
    jmpa @*b6
*b7_zero:
    call @*send_bit_zero

*b6:
    mov rd, rb
    ldi #0x40
    and ra
    mov rd, acc
    cmp zero
    jeq @*b6_zero
    call @*send_bit_one
    jmpa @*b5
*b6_zero:
    call @*send_bit_zero

*b5:
    mov rd, rb
    ldi #0x20
    and ra
    mov rd, acc
    cmp zero
    jeq @*b5_zero
    call @*send_bit_one
    jmpa @*b4
*b5_zero:
    call @*send_bit_zero

*b4:
    mov rd, rb
    ldi #0x10
    and ra
    mov rd, acc
    cmp zero
    jeq @*b4_zero
    call @*send_bit_one
    jmpa @*b3
*b4_zero:
    call @*send_bit_zero

*b3:
    mov rd, rb
    ldi #0x08
    and ra
    mov rd, acc
    cmp zero
    jeq @*b3_zero
    call @*send_bit_one
    jmpa @*b2
*b3_zero:
    call @*send_bit_zero

*b2:
    mov rd, rb
    ldi #0x04
    and ra
    mov rd, acc
    cmp zero
    jeq @*b2_zero
    call @*send_bit_one
    jmpa @*b1
*b2_zero:
    call @*send_bit_zero

*b1:
    mov rd, rb
    ldi #0x02
    and ra
    mov rd, acc
    cmp zero
    jeq @*b1_zero
    call @*send_bit_one
    jmpa @*b0
*b1_zero:
    call @*send_bit_zero

*b0:
    mov rd, rb
    ldi #0x01
    and ra
    mov rd, acc
    cmp zero
    jeq @*b0_zero
    call @*send_bit_one
    ret :stack
*b0_zero:
    call @*send_bit_zero
    ret :stack

*send_bit_zero:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    ldi $OLED_SDA_DRIVE_LOW
    mov m, ra
    call @*pulse_scl
    ret :stack

*send_bit_one:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call @*pulse_scl
    ret :stack

*pulse_scl:
    push lrl
    push lrh

    call @*delay_short
    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    call @*delay_short
    call @*delay_short
    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    ldi $OLED_SCL_DRIVE_LOW
    mov m, ra
    call @*delay_short
    ret :stack

*delay_short:
    ldi rd, $OLED_DELAY_COUNT
*delay_loop:
    subi #1
    mov rd, acc
    jne @*delay_loop
    ret
.endfunc

.export oled_write_command_noack
.func
oled_write_command_noack:
    ; oled_write_command_noack
    ; in :
    ;   RB = command byte
    ; out:
    ;   RB = 0
    ; clobbers:
    ;   RA, RD, ACC, flags, MARL, MARH, PRL, PRH
    ; scratch:
    ;   none
    ;
    ; import note:
    ;   this wrapper calls oled_write_stack_noack, so import both symbols.

    push lrl
    push lrh

    push rb
    ldi #1
    mov rb, ra
    ldi $OLED_CTRL_CMD
    mov rd, ra
    call oled_write_stack_noack
    ret :stack
.endfunc

.export oled_write_data_repeat_noack
.func
oled_write_data_repeat_noack:
    ; oled_write_data_repeat_noack
    ; in :
    ;   RB = repeat count
    ;   RD = byte value to repeat
    ; out:
    ;   RB = 0
    ; clobbers:
    ;   RA, RD, ACC, flags, MARL, MARH, PRL, PRH
    ; scratch:
    ;   F_T0_L = remaining count
    ;   F_T1_L = repeated byte
    ;   F_T2_L = saved return low
    ;   F_T3_L = saved return high

    ldi $F_TMP_BASE_H
    mov marh, ra
    ldi $F_T0_L
    mov marl, ra
    mov m, rb
    ldi $F_T1_L
    mov marl, ra
    mov m, rd
    ldi $F_T2_L
    mov marl, ra
    mov m, lrl
    ldi $F_T3_L
    mov marl, ra
    mov m, lrh

    call @*i2c_start

    ; Slave address + write
    ldi $OLED_ADDR_W
    mov rb, ra
    call @*send_byte
    call @*ack_clock_only

    ; Control byte = data stream
    ldi $OLED_CTRL_DATA
    mov rb, ra
    call @*send_byte
    call @*ack_clock_only

*loop:
    ldi $F_TMP_BASE_H
    mov marh, ra
    ldi $F_T0_L
    mov marl, ra
    mov rd, m
    cmp zero
    jeq @*done

    ldi $F_T1_L
    mov marl, ra
    mov rb, m
    call @*send_byte
    call @*ack_clock_only

    ldi $F_TMP_BASE_H
    mov marh, ra
    ldi $F_T0_L
    mov marl, ra
    mov rd, m
    subi #1
    mov rd, acc
    mov m, rd
    jmpa @*loop

*done:
    call @*i2c_stop
    mov rb, zero
    ldi $F_TMP_BASE_H
    mov marh, ra
    ldi $F_T2_L
    mov marl, ra
    mov ra, m
    mov prl, ra
    ldi $F_T3_L
    mov marl, ra
    mov ra, m
    mov prh, ra
    jmp

*i2c_start:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call @*delay_short

    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    ldi $OLED_SDA_DRIVE_LOW
    mov m, ra
    call @*delay_short

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    ldi $OLED_SCL_DRIVE_LOW
    mov m, ra
    call @*delay_short
    ret :stack

*i2c_stop:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    ldi $OLED_SDA_DRIVE_LOW
    mov m, ra
    call @*delay_short

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    call @*delay_short

    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call @*delay_short
    ret :stack

*ack_clock_only:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call @*delay_short

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    call @*delay_short
    call @*delay_short

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    ldi $OLED_SCL_DRIVE_LOW
    mov m, ra
    call @*delay_short
    ret :stack

*send_byte:
    push lrl
    push lrh

    mov rd, rb
    ldi #0x80
    and ra
    mov rd, acc
    cmp zero
    jeq @*b7_zero
    call @*send_bit_one
    jmpa @*b6
*b7_zero:
    call @*send_bit_zero

*b6:
    mov rd, rb
    ldi #0x40
    and ra
    mov rd, acc
    cmp zero
    jeq @*b6_zero
    call @*send_bit_one
    jmpa @*b5
*b6_zero:
    call @*send_bit_zero

*b5:
    mov rd, rb
    ldi #0x20
    and ra
    mov rd, acc
    cmp zero
    jeq @*b5_zero
    call @*send_bit_one
    jmpa @*b4
*b5_zero:
    call @*send_bit_zero

*b4:
    mov rd, rb
    ldi #0x10
    and ra
    mov rd, acc
    cmp zero
    jeq @*b4_zero
    call @*send_bit_one
    jmpa @*b3
*b4_zero:
    call @*send_bit_zero

*b3:
    mov rd, rb
    ldi #0x08
    and ra
    mov rd, acc
    cmp zero
    jeq @*b3_zero
    call @*send_bit_one
    jmpa @*b2
*b3_zero:
    call @*send_bit_zero

*b2:
    mov rd, rb
    ldi #0x04
    and ra
    mov rd, acc
    cmp zero
    jeq @*b2_zero
    call @*send_bit_one
    jmpa @*b1
*b2_zero:
    call @*send_bit_zero

*b1:
    mov rd, rb
    ldi #0x02
    and ra
    mov rd, acc
    cmp zero
    jeq @*b1_zero
    call @*send_bit_one
    jmpa @*b0
*b1_zero:
    call @*send_bit_zero

*b0:
    mov rd, rb
    ldi #0x01
    and ra
    mov rd, acc
    cmp zero
    jeq @*b0_zero
    call @*send_bit_one
    ret :stack
*b0_zero:
    call @*send_bit_zero
    ret :stack

*send_bit_zero:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    ldi $OLED_SDA_DRIVE_LOW
    mov m, ra
    call @*pulse_scl
    ret :stack

*send_bit_one:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call @*pulse_scl
    ret :stack

*pulse_scl:
    push lrl
    push lrh

    call @*delay_short
    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    call @*delay_short
    call @*delay_short
    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    ldi $OLED_SCL_DRIVE_LOW
    mov m, ra
    call @*delay_short
    ret :stack

*delay_short:
    ldi rd, $OLED_DELAY_COUNT
*delay_loop:
    subi #1
    mov rd, acc
    jne @*delay_loop
    ret
.endfunc

.export oled_fill_screen_noack
.func
oled_fill_screen_noack:
    ; oled_fill_screen_noack
    ; in :
    ;   RB = fill byte
    ; out:
    ;   RB = 0
    ; clobbers:
    ;   RA, RD, ACC, flags, MARL, MARH, PRL, PRH
    ; scratch:
    ;   F_T4_L = fill byte
    ;   F_T5_L = current page command
    ;
    ; import note:
    ;   this routine calls oled_write_stack_noack and oled_write_data_repeat_noack,
    ;   so callers should import all three symbols.

    push lrl
    push lrh

    ldi $F_TMP_BASE_H
    mov marh, ra
    ldi $F_T4_L
    mov marl, ra
    mov m, rb

    ldi #0xB0
    mov rb, ra

*page_loop:
    ; Save current page command.
    ldi $F_TMP_BASE_H
    mov marh, ra
    ldi $F_T5_L
    mov marl, ra
    mov m, rb

    ; Set page and column 0.
    ldi #0x10
    push ra
    ldi #0x00
    push ra
    ldi $F_TMP_BASE_H
    mov marh, ra
    ldi $F_T5_L
    mov marl, ra
    mov ra, m
    push ra
    ldi #3
    mov rb, ra
    ldi $OLED_CTRL_CMD
    mov rd, ra
    call oled_write_stack_noack

    ; Write 128 bytes of the fill value.
    ldi #0x80
    mov rb, ra
    ldi $F_TMP_BASE_H
    mov marh, ra
    ldi $F_T4_L
    mov marl, ra
    mov rd, m
    call oled_write_data_repeat_noack

    ; Next page.
    ldi $F_TMP_BASE_H
    mov marh, ra
    ldi $F_T5_L
    mov marl, ra
    mov rd, m
    addi #1
    mov rb, acc

    ldi #0xB8
    mov rd, rb
    cmp ra
    jne @*page_loop

    mov rb, zero
    ret :stack
.endfunc

.export oled_draw_square
.func
oled_draw_square:
    ; oled_draw_square
    ; in :
    ;   RB = Page Select
    ;   RD = Column Select
    ;   Stack Top = Square size (number of 0xFF bytes)
    ; out:
    ;   RB = 0
    ; clobbers:
    ;   RA, RD, ACC, flags, MARL, MARH, PRL, PRH
    ; import note:
    ;   this routine calls oled_set_page_column_direct,
    ;   oled_begin_data_stream, oled_stream_data_byte,
    ;   and oled_end_stream.
    pop ra
    push ra          ; keep size on stack until the stream is ready

    push lrl
    push lrh

    ; rb = page, rd = column
    call oled_set_page_column_direct 
    mov rd, rb
    cmp zero
    jne *fail

    call oled_begin_data_stream
    mov rd, rb
    cmp zero
    jne *fail

    ; Stack currently holds: [size][saved LRL][saved LRH] with LRH on top.
    ; Recover size without disturbing the return-address pair expected by ret :stack.
    pop rb           ; saved LRH
    pop rd           ; saved LRL
    pop ra           ; size
    push rd          ; restore saved LRL
    push rb          ; restore saved LRH
    mov rd, ra       ; RD = remaining column count

*square_loop:
    cmp zero
    jeq *end_stream

    ldi #0xFF
    mov rb, ra
    push rd
    call oled_stream_data_byte
    pop ra
    mov rd, rb
    cmp zero
    mov rd, ra
    jne *fail

    subi #1
    mov rd, acc
    jmp *square_loop

*end_stream:

    call oled_end_stream
    mov rd, rb
    cmp zero
    jne *fail

*success:
    mov rb, zero
    ret :stack

*fail:
    ret :stack
.endfunc


.export oled_clear_square
.func
oled_clear_square:
    ; oled_clear_square
    ; in :
    ;   RB = Page Select
    ;   RD = Column Select
    ;   Stack Top = Square size (number of 0xFF bytes)
    ; out:
    ;   RB = 0
    ; clobbers:
    ;   RA, RD, ACC, flags, MARL, MARH, PRL, PRH
    ; import note:
    ;   this routine calls oled_set_page_column_direct,
    ;   oled_begin_data_stream, oled_stream_data_byte,
    ;   and oled_end_stream.
    pop ra
    push ra          ; keep size on stack until the stream is ready

    push lrl
    push lrh

    ; rb = page, rd = column
    call oled_set_page_column_direct 
    mov rd, rb
    cmp zero
    jne *fail

    call oled_begin_data_stream
    mov rd, rb
    cmp zero
    jne *fail

    ; Stack currently holds: [size][saved LRL][saved LRH] with LRH on top.
    ; Recover size without disturbing the return-address pair expected by ret :stack.
    pop rb           ; saved LRH
    pop rd           ; saved LRL
    pop ra           ; size
    push rd          ; restore saved LRL
    push rb          ; restore saved LRH
    mov rd, ra       ; RD = remaining column count

*square_loop:
    cmp zero
    jeq *end_stream

    ldi #0x00
    mov rb, ra
    push rd
    call oled_stream_data_byte
    pop ra
    mov rd, rb
    cmp zero
    mov rd, ra
    jne *fail

    subi #1
    mov rd, acc
    jmp *square_loop

*end_stream:

    call oled_end_stream
    mov rd, rb
    cmp zero
    jne *fail

*success:
    mov rb, zero
    ret :stack

*fail:
    ret :stack
.endfunc
