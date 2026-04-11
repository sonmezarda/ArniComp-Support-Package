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
    ;   RB = 0
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

    call oled_wc_i2c_start

    ldi $OLED_ADDR_W
    mov rb, ra
    call oled_wc_send_byte
    call oled_wc_read_ack
    mov rd, rb
    cmp zero
    jne oled_wc_fail_addr

    ldi $OLED_CTRL_CMD
    mov rb, ra
    call oled_wc_send_byte
    call oled_wc_read_ack
    mov rd, rb
    cmp zero
    jne oled_wc_fail_ctrl

    ldi $F_TMP_BASE_H
    mov marh, ra
    ldi $F_T0_L
    mov marl, ra
    mov rb, m
    call oled_wc_send_byte
    call oled_wc_read_ack
    mov rd, rb
    cmp zero
    jne oled_wc_fail_cmd

    call oled_wc_i2c_stop
    mov rb, zero
    ret :stack

oled_wc_fail_addr:
    call oled_wc_i2c_stop
    ldi $OLED_ERR_ADDR
    mov rb, ra
    ret :stack

oled_wc_fail_ctrl:
    call oled_wc_i2c_stop
    ldi $OLED_ERR_CTRL
    mov rb, ra
    ret :stack

oled_wc_fail_cmd:
    call oled_wc_i2c_stop
    ldi $OLED_ERR_CMD
    mov rb, ra
    ret :stack

oled_wc_i2c_start:
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
    call oled_wc_delay_short

    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    ldi $OLED_SDA_DRIVE_LOW
    mov m, ra
    call oled_wc_delay_short

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    ldi $OLED_SCL_DRIVE_LOW
    mov m, ra
    call oled_wc_delay_short
    ret :stack

oled_wc_i2c_stop:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra

    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    ldi $OLED_SDA_DRIVE_LOW
    mov m, ra
    call oled_wc_delay_short

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    call oled_wc_delay_short

    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call oled_wc_delay_short
    ret :stack

oled_wc_read_ack:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call oled_wc_delay_short

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    call oled_wc_delay_short
    call oled_wc_delay_short

    ldi $OLED_GPIO_IN1_L
    mov marl, ra
    mov rd, m
    mov rb, rd

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    ldi $OLED_SCL_DRIVE_LOW
    mov m, ra
    call oled_wc_delay_short
    ret :stack

oled_wc_send_byte:
    push lrl
    push lrh

    mov rd, rb
    ldi #0x80
    and ra
    mov rd, acc
    cmp zero
    jeq oled_wc_b7_zero
    call oled_wc_send_bit_one
    jmp oled_wc_b6
oled_wc_b7_zero:
    call oled_wc_send_bit_zero

oled_wc_b6:
    mov rd, rb
    ldi #0x40
    and ra
    mov rd, acc
    cmp zero
    jeq oled_wc_b6_zero
    call oled_wc_send_bit_one
    jmp oled_wc_b5
oled_wc_b6_zero:
    call oled_wc_send_bit_zero

oled_wc_b5:
    mov rd, rb
    ldi #0x20
    and ra
    mov rd, acc
    cmp zero
    jeq oled_wc_b5_zero
    call oled_wc_send_bit_one
    jmp oled_wc_b4
oled_wc_b5_zero:
    call oled_wc_send_bit_zero

oled_wc_b4:
    mov rd, rb
    ldi #0x10
    and ra
    mov rd, acc
    cmp zero
    jeq oled_wc_b4_zero
    call oled_wc_send_bit_one
    jmp oled_wc_b3
oled_wc_b4_zero:
    call oled_wc_send_bit_zero

oled_wc_b3:
    mov rd, rb
    ldi #0x08
    and ra
    mov rd, acc
    cmp zero
    jeq oled_wc_b3_zero
    call oled_wc_send_bit_one
    jmp oled_wc_b2
oled_wc_b3_zero:
    call oled_wc_send_bit_zero

oled_wc_b2:
    mov rd, rb
    ldi #0x04
    and ra
    mov rd, acc
    cmp zero
    jeq oled_wc_b2_zero
    call oled_wc_send_bit_one
    jmp oled_wc_b1
oled_wc_b2_zero:
    call oled_wc_send_bit_zero

oled_wc_b1:
    mov rd, rb
    ldi #0x02
    and ra
    mov rd, acc
    cmp zero
    jeq oled_wc_b1_zero
    call oled_wc_send_bit_one
    jmp oled_wc_b0
    nop
    nop
    nop
    nop
    nop
oled_wc_b1_zero:
    call oled_wc_send_bit_zero

oled_wc_b0:
    mov rd, rb
    ldi #0x01
    and ra
    mov rd, acc
    cmp zero
    jeq oled_wc_b0_zero
    call oled_wc_send_bit_one
    ret :stack
oled_wc_b0_zero:
    call oled_wc_send_bit_zero
    ret :stack

oled_wc_send_bit_zero:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    ldi $OLED_SDA_DRIVE_LOW
    mov m, ra
    call oled_wc_pulse_scl
    ret :stack

oled_wc_send_bit_one:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call oled_wc_pulse_scl
    ret :stack

oled_wc_pulse_scl:
    push lrl
    push lrh

    call oled_wc_delay_short
    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    call oled_wc_delay_short
    call oled_wc_delay_short
    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    ldi $OLED_SCL_DRIVE_LOW
    mov m, ra
    call oled_wc_delay_short
    ret :stack

oled_wc_delay_short:
    ldi rd, $OLED_DELAY_COUNT
oled_wc_delay_loop:
    subi #1
    mov rd, acc
    jne oled_wc_delay_loop
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

    call oled_bds_i2c_start

    ldi $OLED_ADDR_W
    mov rb, ra
    call oled_bds_send_byte
    call oled_bds_read_ack
    mov rd, rb
    cmp zero
    jne oled_bds_fail_addr

    ldi $OLED_CTRL_DATA
    mov rb, ra
    call oled_bds_send_byte
    call oled_bds_read_ack
    mov rd, rb
    cmp zero
    jne oled_bds_fail_ctrl

    mov rb, zero
    ret :stack

oled_bds_fail_addr:
    call oled_bds_i2c_stop
    ldi $OLED_ERR_ADDR
    mov rb, ra
    ret :stack

oled_bds_fail_ctrl:
    call oled_bds_i2c_stop
    ldi $OLED_ERR_CTRL
    mov rb, ra
    ret :stack

oled_bds_i2c_start:
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
    call oled_bds_delay_short

    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    ldi $OLED_SDA_DRIVE_LOW
    mov m, ra
    call oled_bds_delay_short

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    ldi $OLED_SCL_DRIVE_LOW
    mov m, ra
    call oled_bds_delay_short
    ret :stack

oled_bds_i2c_stop:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra

    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    ldi $OLED_SDA_DRIVE_LOW
    mov m, ra
    call oled_bds_delay_short

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    call oled_bds_delay_short

    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call oled_bds_delay_short
    ret :stack

oled_bds_read_ack:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call oled_bds_delay_short

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    call oled_bds_delay_short
    call oled_bds_delay_short

    ldi $OLED_GPIO_IN1_L
    mov marl, ra
    mov rd, m
    mov rb, rd

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    ldi $OLED_SCL_DRIVE_LOW
    mov m, ra
    call oled_bds_delay_short
    ret :stack

oled_bds_send_byte:
    push lrl
    push lrh

    mov rd, rb
    ldi #0x80
    and ra
    mov rd, acc
    cmp zero
    jeq oled_bds_b7_zero
    call oled_bds_send_bit_one
    jmp oled_bds_b6
oled_bds_b7_zero:
    call oled_bds_send_bit_zero

oled_bds_b6:
    mov rd, rb
    ldi #0x40
    and ra
    mov rd, acc
    cmp zero
    jeq oled_bds_b6_zero
    call oled_bds_send_bit_one
    jmp oled_bds_b5
oled_bds_b6_zero:
    call oled_bds_send_bit_zero

oled_bds_b5:
    mov rd, rb
    ldi #0x20
    and ra
    mov rd, acc
    cmp zero
    jeq oled_bds_b5_zero
    call oled_bds_send_bit_one
    jmp oled_bds_b4
oled_bds_b5_zero:
    call oled_bds_send_bit_zero

oled_bds_b4:
    mov rd, rb
    ldi #0x10
    and ra
    mov rd, acc
    cmp zero
    jeq oled_bds_b4_zero
    call oled_bds_send_bit_one
    jmp oled_bds_b3
oled_bds_b4_zero:
    call oled_bds_send_bit_zero

oled_bds_b3:
    mov rd, rb
    ldi #0x08
    and ra
    mov rd, acc
    cmp zero
    jeq oled_bds_b3_zero
    call oled_bds_send_bit_one
    jmp oled_bds_b2
oled_bds_b3_zero:
    call oled_bds_send_bit_zero

oled_bds_b2:
    mov rd, rb
    ldi #0x04
    and ra
    mov rd, acc
    cmp zero
    jeq oled_bds_b2_zero
    call oled_bds_send_bit_one
    jmp oled_bds_b1
oled_bds_b2_zero:
    call oled_bds_send_bit_zero

oled_bds_b1:
    mov rd, rb
    ldi #0x02
    and ra
    mov rd, acc
    cmp zero
    jeq oled_bds_b1_zero
    call oled_bds_send_bit_one
    jmp oled_bds_b0
    nop
    nop
    nop
    nop
    nop
oled_bds_b1_zero:
    call oled_bds_send_bit_zero

oled_bds_b0:
    mov rd, rb
    ldi #0x01
    and ra
    mov rd, acc
    cmp zero
    jeq oled_bds_b0_zero
    call oled_bds_send_bit_one
    ret :stack
oled_bds_b0_zero:
    call oled_bds_send_bit_zero
    ret :stack

oled_bds_send_bit_zero:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    ldi $OLED_SDA_DRIVE_LOW
    mov m, ra
    call oled_bds_pulse_scl
    ret :stack

oled_bds_send_bit_one:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call oled_bds_pulse_scl
    ret :stack

oled_bds_pulse_scl:
    push lrl
    push lrh

    call oled_bds_delay_short
    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    call oled_bds_delay_short
    call oled_bds_delay_short
    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    ldi $OLED_SCL_DRIVE_LOW
    mov m, ra
    call oled_bds_delay_short
    ret :stack

oled_bds_delay_short:
    ldi rd, $OLED_DELAY_COUNT
oled_bds_delay_loop:
    subi #1
    mov rd, acc
    jne oled_bds_delay_loop
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

    call oled_sdb_send_byte
    call oled_sdb_read_ack
    mov rd, rb
    cmp zero
    jne oled_sdb_fail_data

    mov rb, zero
    ret :stack

oled_sdb_fail_data:
    call oled_sdb_i2c_stop
    ldi $OLED_ERR_DATA
    mov rb, ra
    ret :stack

oled_sdb_i2c_stop:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra

    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    ldi $OLED_SDA_DRIVE_LOW
    mov m, ra
    call oled_sdb_delay_short

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    call oled_sdb_delay_short

    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call oled_sdb_delay_short
    ret :stack

oled_sdb_read_ack:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call oled_sdb_delay_short

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    call oled_sdb_delay_short
    call oled_sdb_delay_short

    ldi $OLED_GPIO_IN1_L
    mov marl, ra
    mov rd, m
    mov rb, rd

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    ldi $OLED_SCL_DRIVE_LOW
    mov m, ra
    call oled_sdb_delay_short
    ret :stack

oled_sdb_send_byte:
    push lrl
    push lrh

    mov rd, rb
    ldi #0x80
    and ra
    mov rd, acc
    cmp zero
    jeq oled_sdb_b7_zero
    call oled_sdb_send_bit_one
    jmp oled_sdb_b6
oled_sdb_b7_zero:
    call oled_sdb_send_bit_zero

oled_sdb_b6:
    mov rd, rb
    ldi #0x40
    and ra
    mov rd, acc
    cmp zero
    jeq oled_sdb_b6_zero
    call oled_sdb_send_bit_one
    jmp oled_sdb_b5
oled_sdb_b6_zero:
    call oled_sdb_send_bit_zero

oled_sdb_b5:
    mov rd, rb
    ldi #0x20
    and ra
    mov rd, acc
    cmp zero
    jeq oled_sdb_b5_zero
    call oled_sdb_send_bit_one
    jmp oled_sdb_b4
oled_sdb_b5_zero:
    call oled_sdb_send_bit_zero

oled_sdb_b4:
    mov rd, rb
    ldi #0x10
    and ra
    mov rd, acc
    cmp zero
    jeq oled_sdb_b4_zero
    call oled_sdb_send_bit_one
    jmp oled_sdb_b3
oled_sdb_b4_zero:
    call oled_sdb_send_bit_zero

oled_sdb_b3:
    mov rd, rb
    ldi #0x08
    and ra
    mov rd, acc
    cmp zero
    jeq oled_sdb_b3_zero
    call oled_sdb_send_bit_one
    jmp oled_sdb_b2
oled_sdb_b3_zero:
    call oled_sdb_send_bit_zero

oled_sdb_b2:
    mov rd, rb
    ldi #0x04
    and ra
    mov rd, acc
    cmp zero
    jeq oled_sdb_b2_zero
    call oled_sdb_send_bit_one
    jmp oled_sdb_b1
oled_sdb_b2_zero:
    call oled_sdb_send_bit_zero

oled_sdb_b1:
    mov rd, rb
    ldi #0x02
    and ra
    mov rd, acc
    cmp zero
    jeq oled_sdb_b1_zero
    call oled_sdb_send_bit_one
    jmp oled_sdb_b0
    nop
    nop
    nop
    nop
    nop
oled_sdb_b1_zero:
    call oled_sdb_send_bit_zero

oled_sdb_b0:
    mov rd, rb
    ldi #0x01
    and ra
    mov rd, acc
    cmp zero
    jeq oled_sdb_b0_zero
    call oled_sdb_send_bit_one
    ret :stack
oled_sdb_b0_zero:
    call oled_sdb_send_bit_zero
    ret :stack

oled_sdb_send_bit_zero:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    ldi $OLED_SDA_DRIVE_LOW
    mov m, ra
    call oled_sdb_pulse_scl
    ret :stack

oled_sdb_send_bit_one:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call oled_sdb_pulse_scl
    ret :stack

oled_sdb_pulse_scl:
    push lrl
    push lrh

    call oled_sdb_delay_short
    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    call oled_sdb_delay_short
    call oled_sdb_delay_short
    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    ldi $OLED_SCL_DRIVE_LOW
    mov m, ra
    call oled_sdb_delay_short
    ret :stack

oled_sdb_delay_short:
    ldi rd, $OLED_DELAY_COUNT
oled_sdb_delay_loop:
    subi #1
    mov rd, acc
    jne oled_sdb_delay_loop
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
    call oled_es_delay_short

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    call oled_es_delay_short

    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call oled_es_delay_short

    mov rb, zero
    ret :stack

oled_es_delay_short:
    ldi rd, $OLED_DELAY_COUNT
oled_es_delay_loop:
    subi #1
    mov rd, acc
    jne oled_es_delay_loop
    ret
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

oled_fill_screen_page_loop:
    ldi $F_TMP_BASE_H
    mov marh, ra
    ldi $F_T5_L
    mov marl, ra
    mov rb, m
    call oled_write_command
    mov rd, rb
    cmp zero
    jne oled_fill_screen_fail

    ldi #0x00
    mov rb, ra
    call oled_write_command
    mov rd, rb
    cmp zero
    jne oled_fill_screen_fail

    ldi #0x10
    mov rb, ra
    call oled_write_command
    mov rd, rb
    cmp zero
    jne oled_fill_screen_fail

    call oled_begin_data_stream
    mov rd, rb
    cmp zero
    jne oled_fill_screen_fail

    ldi $F_TMP_BASE_H
    mov marh, ra
    ldi $F_T6_L
    mov marl, ra
    ldi #0x80
    mov m, ra

oled_fill_screen_data_loop:
    ldi $F_TMP_BASE_H
    mov marh, ra
    ldi $F_T4_L
    mov marl, ra
    mov rb, m
    call oled_stream_data_byte
    mov rd, rb
    cmp zero
    jne oled_fill_screen_fail

    ldi $F_TMP_BASE_H
    mov marh, ra
    ldi $F_T6_L
    mov marl, ra
    mov rd, m
    subi #1
    mov rd, acc
    mov m, rd
    jne oled_fill_screen_data_loop

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
    jne oled_fill_screen_page_loop

    mov rb, zero
    ret :stack

oled_fill_screen_fail:
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

    call oled_ws_i2c_start

    ; Slave address + write
    ldi $OLED_ADDR_W
    mov rb, ra
    call oled_ws_send_byte
    call oled_ws_ack_clock_only

    ; Control byte
    ldi $F_TMP_BASE_H
    mov marh, ra
    ldi $F_T1_L
    mov marl, ra
    mov rb, m
    call oled_ws_send_byte
    call oled_ws_ack_clock_only

oled_ws_loop:
    ldi $F_TMP_BASE_H
    mov marh, ra
    ldi $F_T0_L
    mov marl, ra
    mov rd, m
    cmp zero
    jeq oled_ws_done

    pop rb
    call oled_ws_send_byte
    call oled_ws_ack_clock_only

    ldi $F_TMP_BASE_H
    mov marh, ra
    ldi $F_T0_L
    mov marl, ra
    mov rd, m
    subi #1
    mov rd, acc
    mov m, rd
    jmpa oled_ws_loop

oled_ws_done:
    call oled_ws_i2c_stop
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

oled_ws_i2c_start:
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
    call oled_ws_delay_short

    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    ldi $OLED_SDA_DRIVE_LOW
    mov m, ra
    call oled_ws_delay_short

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    ldi $OLED_SCL_DRIVE_LOW
    mov m, ra
    call oled_ws_delay_short
    ret :stack

oled_ws_i2c_stop:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra

    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    ldi $OLED_SDA_DRIVE_LOW
    mov m, ra
    call oled_ws_delay_short

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    call oled_ws_delay_short

    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call oled_ws_delay_short
    ret :stack

oled_ws_ack_clock_only:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra

    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call oled_ws_delay_short

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    call oled_ws_delay_short
    call oled_ws_delay_short

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    ldi $OLED_SCL_DRIVE_LOW
    mov m, ra
    call oled_ws_delay_short
    ret :stack

oled_ws_send_byte:
    ; In: RB = byte to send, MSB first.
    push lrl
    push lrh

    mov rd, rb
    ldi #0x80
    and ra
    mov rd, acc
    cmp zero
    jeq oled_ws_b7_zero
    call oled_ws_send_bit_one
    jmpa oled_ws_b6
oled_ws_b7_zero:
    call oled_ws_send_bit_zero

oled_ws_b6:
    mov rd, rb
    ldi #0x40
    and ra
    mov rd, acc
    cmp zero
    jeq oled_ws_b6_zero
    call oled_ws_send_bit_one
    jmpa oled_ws_b5
oled_ws_b6_zero:
    call oled_ws_send_bit_zero

oled_ws_b5:
    mov rd, rb
    ldi #0x20
    and ra
    mov rd, acc
    cmp zero
    jeq oled_ws_b5_zero
    call oled_ws_send_bit_one
    jmpa oled_ws_b4
oled_ws_b5_zero:
    call oled_ws_send_bit_zero

oled_ws_b4:
    mov rd, rb
    ldi #0x10
    and ra
    mov rd, acc
    cmp zero
    jeq oled_ws_b4_zero
    call oled_ws_send_bit_one
    jmpa oled_ws_b3
oled_ws_b4_zero:
    call oled_ws_send_bit_zero

oled_ws_b3:
    mov rd, rb
    ldi #0x08
    and ra
    mov rd, acc
    cmp zero
    jeq oled_ws_b3_zero
    call oled_ws_send_bit_one
    jmpa oled_ws_b2
oled_ws_b3_zero:
    call oled_ws_send_bit_zero

oled_ws_b2:
    mov rd, rb
    ldi #0x04
    and ra
    mov rd, acc
    cmp zero
    jeq oled_ws_b2_zero
    call oled_ws_send_bit_one
    jmpa oled_ws_b1
oled_ws_b2_zero:
    call oled_ws_send_bit_zero

oled_ws_b1:
    mov rd, rb
    ldi #0x02
    and ra
    mov rd, acc
    cmp zero
    jeq oled_ws_b1_zero
    call oled_ws_send_bit_one
    jmpa oled_ws_b0
oled_ws_b1_zero:
    call oled_ws_send_bit_zero

oled_ws_b0:
    mov rd, rb
    ldi #0x01
    and ra
    mov rd, acc
    cmp zero
    jeq oled_ws_b0_zero
    call oled_ws_send_bit_one
    ret :stack
oled_ws_b0_zero:
    call oled_ws_send_bit_zero
    ret :stack

oled_ws_send_bit_zero:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    ldi $OLED_SDA_DRIVE_LOW
    mov m, ra
    call oled_ws_pulse_scl
    ret :stack

oled_ws_send_bit_one:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call oled_ws_pulse_scl
    ret :stack

oled_ws_pulse_scl:
    push lrl
    push lrh

    call oled_ws_delay_short
    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    call oled_ws_delay_short
    call oled_ws_delay_short
    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    ldi $OLED_SCL_DRIVE_LOW
    mov m, ra
    call oled_ws_delay_short
    ret :stack

oled_ws_delay_short:
    ldi rd, $OLED_DELAY_COUNT
oled_ws_delay_loop:
    subi #1
    mov rd, acc
    jne oled_ws_delay_loop
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

    call oled_wdr_i2c_start

    ; Slave address + write
    ldi $OLED_ADDR_W
    mov rb, ra
    call oled_wdr_send_byte
    call oled_wdr_ack_clock_only

    ; Control byte = data stream
    ldi $OLED_CTRL_DATA
    mov rb, ra
    call oled_wdr_send_byte
    call oled_wdr_ack_clock_only

oled_wdr_loop:
    ldi $F_TMP_BASE_H
    mov marh, ra
    ldi $F_T0_L
    mov marl, ra
    mov rd, m
    cmp zero
    jeq oled_wdr_done

    ldi $F_T1_L
    mov marl, ra
    mov rb, m
    call oled_wdr_send_byte
    call oled_wdr_ack_clock_only

    ldi $F_TMP_BASE_H
    mov marh, ra
    ldi $F_T0_L
    mov marl, ra
    mov rd, m
    subi #1
    mov rd, acc
    mov m, rd
    jmpa oled_wdr_loop

oled_wdr_done:
    call oled_wdr_i2c_stop
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

oled_wdr_i2c_start:
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
    call oled_wdr_delay_short

    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    ldi $OLED_SDA_DRIVE_LOW
    mov m, ra
    call oled_wdr_delay_short

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    ldi $OLED_SCL_DRIVE_LOW
    mov m, ra
    call oled_wdr_delay_short
    ret :stack

oled_wdr_i2c_stop:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    ldi $OLED_SDA_DRIVE_LOW
    mov m, ra
    call oled_wdr_delay_short

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    call oled_wdr_delay_short

    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call oled_wdr_delay_short
    ret :stack

oled_wdr_ack_clock_only:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call oled_wdr_delay_short

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    call oled_wdr_delay_short
    call oled_wdr_delay_short

    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    ldi $OLED_SCL_DRIVE_LOW
    mov m, ra
    call oled_wdr_delay_short
    ret :stack

oled_wdr_send_byte:
    push lrl
    push lrh

    mov rd, rb
    ldi #0x80
    and ra
    mov rd, acc
    cmp zero
    jeq oled_wdr_b7_zero
    call oled_wdr_send_bit_one
    jmpa oled_wdr_b6
oled_wdr_b7_zero:
    call oled_wdr_send_bit_zero

oled_wdr_b6:
    mov rd, rb
    ldi #0x40
    and ra
    mov rd, acc
    cmp zero
    jeq oled_wdr_b6_zero
    call oled_wdr_send_bit_one
    jmpa oled_wdr_b5
oled_wdr_b6_zero:
    call oled_wdr_send_bit_zero

oled_wdr_b5:
    mov rd, rb
    ldi #0x20
    and ra
    mov rd, acc
    cmp zero
    jeq oled_wdr_b5_zero
    call oled_wdr_send_bit_one
    jmpa oled_wdr_b4
oled_wdr_b5_zero:
    call oled_wdr_send_bit_zero

oled_wdr_b4:
    mov rd, rb
    ldi #0x10
    and ra
    mov rd, acc
    cmp zero
    jeq oled_wdr_b4_zero
    call oled_wdr_send_bit_one
    jmpa oled_wdr_b3
oled_wdr_b4_zero:
    call oled_wdr_send_bit_zero

oled_wdr_b3:
    mov rd, rb
    ldi #0x08
    and ra
    mov rd, acc
    cmp zero
    jeq oled_wdr_b3_zero
    call oled_wdr_send_bit_one
    jmpa oled_wdr_b2
oled_wdr_b3_zero:
    call oled_wdr_send_bit_zero

oled_wdr_b2:
    mov rd, rb
    ldi #0x04
    and ra
    mov rd, acc
    cmp zero
    jeq oled_wdr_b2_zero
    call oled_wdr_send_bit_one
    jmpa oled_wdr_b1
oled_wdr_b2_zero:
    call oled_wdr_send_bit_zero

oled_wdr_b1:
    mov rd, rb
    ldi #0x02
    and ra
    mov rd, acc
    cmp zero
    jeq oled_wdr_b1_zero
    call oled_wdr_send_bit_one
    jmpa oled_wdr_b0
oled_wdr_b1_zero:
    call oled_wdr_send_bit_zero

oled_wdr_b0:
    mov rd, rb
    ldi #0x01
    and ra
    mov rd, acc
    cmp zero
    jeq oled_wdr_b0_zero
    call oled_wdr_send_bit_one
    ret :stack
oled_wdr_b0_zero:
    call oled_wdr_send_bit_zero
    ret :stack

oled_wdr_send_bit_zero:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    ldi $OLED_SDA_DRIVE_LOW
    mov m, ra
    call oled_wdr_pulse_scl
    ret :stack

oled_wdr_send_bit_one:
    push lrl
    push lrh

    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR1_L
    mov marl, ra
    mov m, zero
    call oled_wdr_pulse_scl
    ret :stack

oled_wdr_pulse_scl:
    push lrl
    push lrh

    call oled_wdr_delay_short
    ldi $OLED_GPIO_BASE_H
    mov marh, ra
    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    mov m, zero
    call oled_wdr_delay_short
    call oled_wdr_delay_short
    ldi $OLED_GPIO_DIR0_L
    mov marl, ra
    ldi $OLED_SCL_DRIVE_LOW
    mov m, ra
    call oled_wdr_delay_short
    ret :stack

oled_wdr_delay_short:
    ldi rd, $OLED_DELAY_COUNT
oled_wdr_delay_loop:
    subi #1
    mov rd, acc
    jne oled_wdr_delay_loop
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

oled_fill_page_loop:
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
    jne oled_fill_page_loop

    mov rb, zero
    ret :stack
.endfunc
