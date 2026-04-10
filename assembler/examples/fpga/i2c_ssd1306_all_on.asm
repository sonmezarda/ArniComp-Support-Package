; Minimal SSD1306 bring-up using the Gowin I2C master IP.
;
; This version intentionally mirrors the software-I2C flow that already
; worked on hardware: every OLED command is sent as its own transaction:
;   START + address
;   control byte (0x00 = command stream)
;   command byte + STOP
;
; Wiring:
; - Tang Nano 9K top uses direct 27 MHz cpu_clk
; - Gowin I2C SCL -> pin 25
; - Gowin I2C SDA -> pin 26
; - OLED 7-bit address = 0x3C, so write byte = 0x78

equ SYS_LED_H          0x0C
equ SYS_LED_L          0x00
equ LED_OK             0x01
equ LED_FAIL_ADDR      0x02
equ LED_FAIL_CTRL      0x03
equ LED_FAIL_CMD       0x04
equ LED_FAIL_TIMEOUT   0x08
equ LED_FAIL_AL        0x10

equ I2C_BASE_H         0x0A
equ I2C_PRESCALE_LO    0x00
equ I2C_PRESCALE_HI    0x01
equ I2C_CONTROL        0x02
equ I2C_TXR            0x03
equ I2C_CR_SR          0x04

equ RAM_BASE_H         0x00
equ SCRATCH_CMD_L      0x00
equ SCRATCH_COUNT_L    0x01

equ PRESCALE_100KHZ    0x35
equ CTRL_ENABLE        0x80
equ OLED_ADDR_W        0x78
equ OLED_CTRL_CMD      0x00

equ CMD_START_WRITE    0x90
equ CMD_WRITE          0x10
equ CMD_STOP_WRITE     0x50
equ CMD_STOP_ONLY      0x40

equ RXACK_MASK         0x80
equ BUSY_MASK          0x40
equ AL_MASK            0x20
equ TIP_MASK           0x02
equ WAIT_TIMEOUT       0xFF
equ WAIT_COUNT         200

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

    ldi $I2C_BASE_H
    mov marh, ra

    ldi $I2C_PRESCALE_LO
    mov marl, ra
    ldi $PRESCALE_100KHZ
    mov m, ra

    ldi $I2C_PRESCALE_HI
    mov marl, ra
    mov m, zero

    ldi $I2C_CONTROL
    mov marl, ra
    ldi $CTRL_ENABLE
    mov m, ra

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
    ; Out: RB = 0 on success, LED_FAIL_* on failure
    push lrl
    push lrh

    ldi $RAM_BASE_H
    mov marh, ra
    ldi $SCRATCH_CMD_L
    mov marl, ra
    mov m, rb

    ; Address phase
    ldi $OLED_ADDR_W
    mov rb, ra
    ldi $CMD_START_WRITE
    mov rd, ra
    call write_txr_cr_wait
    call check_common_status
    mov rd, rb
    cmp zero
    jne write_fail_addr_stop

    ; Control phase
    ldi $OLED_CTRL_CMD
    mov rb, ra
    ldi $CMD_WRITE
    mov rd, ra
    call write_txr_cr_wait
    call check_common_status
    mov rd, rb
    cmp zero
    jne write_fail_ctrl_stop

    ; Command phase with STOP
    ldi $RAM_BASE_H
    mov marh, ra
    ldi $SCRATCH_CMD_L
    mov marl, ra
    mov rb, m

    ldi $CMD_STOP_WRITE
    mov rd, ra
    call write_txr_cr_wait
    call check_common_status
    mov rd, rb
    cmp zero
    jne write_fail_cmd

    call wait_bus_idle
    mov rd, rb
    ldi $WAIT_TIMEOUT
    cmp ra
    jeq write_fail_timeout

    mov rd, rb
    ldi $AL_MASK
    and ra
    mov rd, acc
    cmp zero
    jne write_fail_al

    mov rb, zero
    ret :stack

write_fail_addr_stop:
    call issue_stop
    ldi $LED_FAIL_ADDR
    mov rb, ra
    ret :stack

write_fail_ctrl_stop:
    call issue_stop
    ldi $LED_FAIL_CTRL
    mov rb, ra
    ret :stack

write_fail_cmd:
    ldi $LED_FAIL_CMD
    mov rb, ra
    ret :stack

write_fail_timeout:
    ldi $LED_FAIL_TIMEOUT
    mov rb, ra
    ret :stack

write_fail_al:
    ldi $LED_FAIL_AL
    mov rb, ra
    ret :stack

write_txr_cr_wait:
    ; In:
    ; - RB = byte to place in TXR
    ; - RD = command value to place in CR
    ; Out:
    ; - RB = status on success, 0xFF on timeout
    push lrl
    push lrh

    ldi $I2C_BASE_H
    mov marh, ra

    ldi $I2C_TXR
    mov marl, ra
    mov m, rb

    ldi $I2C_CR_SR
    mov marl, ra
    mov m, rd

    call wait_done
    ret :stack

check_common_status:
    ; In:  RB = status or 0xFF timeout marker
    ; Out: RB = 0 on success, 1 on failure
    push lrl
    push lrh

    mov rd, rb
    ldi $WAIT_TIMEOUT
    cmp ra
    jeq check_status_fail

    mov rd, rb
    ldi $AL_MASK
    and ra
    mov rd, acc
    cmp zero
    jne check_status_fail

    mov rd, rb
    ldi $RXACK_MASK
    and ra
    mov rd, acc
    cmp zero
    jne check_status_fail

    mov rb, zero
    ret :stack

check_status_fail:
    ldi #1
    mov rb, ra
    ret :stack

issue_stop:
    push lrl
    push lrh

    ldi $I2C_BASE_H
    mov marh, ra
    ldi $I2C_CR_SR
    mov marl, ra
    ldi $CMD_STOP_ONLY
    mov m, ra
    ret :stack

wait_done:
    ; Out: RB = status on success, 0xFF on timeout
    push lrl
    push lrh

    ldi $RAM_BASE_H
    mov marh, ra
    ldi $SCRATCH_COUNT_L
    mov marl, ra
    ldi $WAIT_COUNT
    mov m, ra

wait_done_loop:
    ldi $I2C_BASE_H
    mov marh, ra
    ldi $I2C_CR_SR
    mov marl, ra
    mov rb, m

    mov rd, rb
    ldi $AL_MASK
    and ra
    mov rd, acc
    cmp zero
    jne wait_done_ok

    mov rd, rb
    ldi $TIP_MASK
    and ra
    mov rd, acc
    cmp zero
    jeq wait_done_ok

    ldi $RAM_BASE_H
    mov marh, ra
    ldi $SCRATCH_COUNT_L
    mov marl, ra
    mov rd, m
    subi #1
    mov rd, acc
    mov m, rd
    jne wait_done_loop

    ldi $WAIT_TIMEOUT
    mov rb, ra
    ret :stack

wait_done_ok:
    ret :stack

wait_bus_idle:
    ; Out: RB = status on success, 0xFF on timeout
    push lrl
    push lrh

    ldi $RAM_BASE_H
    mov marh, ra
    ldi $SCRATCH_COUNT_L
    mov marl, ra
    ldi $WAIT_COUNT
    mov m, ra

wait_bus_idle_loop:
    ldi $I2C_BASE_H
    mov marh, ra
    ldi $I2C_CR_SR
    mov marl, ra
    mov rb, m

    mov rd, rb
    ldi $AL_MASK
    and ra
    mov rd, acc
    cmp zero
    jne wait_bus_idle_ok

    mov rd, rb
    ldi $BUSY_MASK
    and ra
    mov rd, acc
    cmp zero
    jeq wait_bus_idle_ok

    ldi $RAM_BASE_H
    mov marh, ra
    ldi $SCRATCH_COUNT_L
    mov marl, ra
    mov rd, m
    subi #1
    mov rd, acc
    mov m, rd
    jne wait_bus_idle_loop

    ldi $WAIT_TIMEOUT
    mov rb, ra
    ret :stack

wait_bus_idle_ok:
    ret :stack

done:
    jmpa done
