; Gowin I2C two-byte snapshot:
; - sends address byte with START
; - sends control byte 0x00
; - captures the raw status after the control phase
; - writes a compact status view to SYS LEDs
;
; LED mapping written into SYS_LED[5:0]:
; - bit0 -> IF
; - bit1 -> TIP
; - bit2 -> BUSY
; - bit3 -> AL
; - bit4 -> RX_ACK (1 = NACK)
; - bit5 -> timeout or address-phase failure marker

equ SYS_LED_H        0x0C
equ SYS_LED_L        0x00

equ I2C_BASE_H       0x0A
equ I2C_PRESCALE_LO  0x00
equ I2C_PRESCALE_HI  0x01
equ I2C_CONTROL      0x02
equ I2C_TXR          0x03
equ I2C_CR_SR        0x04

equ RAM_BASE_H       0x00
equ SCRATCH_COUNT_L  0x00
equ SCRATCH_STATUS_L 0x01

equ PRESCALE_100KHZ  0x35
equ CTRL_ENABLE      0x80
equ OLED_ADDR_W      0x78
equ OLED_CTRL_CMD    0x00

equ CMD_START_WRITE  0x90
equ CMD_WRITE        0x10
equ CMD_STOP_ONLY    0x40

equ IF_MASK          0x01
equ TIP_MASK         0x02
equ BUSY_MASK        0x40
equ AL_MASK          0x20
equ RXACK_MASK       0x80
equ WAIT_TIMEOUT     0xFF
equ WAIT_COUNT       200

equ LED_IF           0x01
equ LED_TIP          0x02
equ LED_BUSY         0x04
equ LED_AL           0x08
equ LED_RXACK        0x10
equ LED_MARKER       0x20

setup:
    mov prh, zero
    mov prl, zero
    mov marl, zero
    mov marh, zero
    mov rb, zero

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

    ; Address phase
    ldi $I2C_TXR
    mov marl, ra
    ldi $OLED_ADDR_W
    mov m, ra

    ldi $I2C_CR_SR
    mov marl, ra
    ldi $CMD_START_WRITE
    mov m, ra

    call wait_done
    mov rd, rb
    ldi $WAIT_TIMEOUT
    cmp ra
    jeq show_timeout

    mov rd, rb
    ldi $AL_MASK
    and ra
    mov rd, acc
    cmp zero
    jne show_addr_failure

    mov rd, rb
    ldi $RXACK_MASK
    and ra
    mov rd, acc
    cmp zero
    jne show_addr_failure

    ; Control-byte phase
    ldi $I2C_BASE_H
    mov marh, ra
    ldi $I2C_TXR
    mov marl, ra
    ldi $OLED_CTRL_CMD
    mov m, ra

    ldi $I2C_CR_SR
    mov marl, ra
    ldi $CMD_WRITE
    mov m, ra

    call wait_done
    mov rd, rb
    ldi $WAIT_TIMEOUT
    cmp ra
    jeq show_timeout

    call issue_stop
    jmp capture_status

show_addr_failure:
    ; Show the address-phase raw status plus a marker in bit5.
    call pack_status_leds
    ldi rd, $LED_MARKER
    add rb
    mov rb, acc
    jmp show_leds

show_timeout:
    ldi $LED_MARKER
    mov rb, ra
    jmp show_leds

capture_status:
    ldi $I2C_BASE_H
    mov marh, ra
    ldi $I2C_CR_SR
    mov marl, ra
    mov rb, m

    call pack_status_leds

show_leds:
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    mov m, rb

done:
    jmpa done

pack_status_leds:
    ; In:  RB = raw status
    ; Out: RB = compact LED image
    push lrl
    push lrh

    ldi $RAM_BASE_H
    mov marh, ra
    ldi $SCRATCH_STATUS_L
    mov marl, ra
    mov m, rb

    mov rb, zero

    mov ra, m
    ldi rd, $IF_MASK
    and ra
    mov ra, acc
    cmp zero
    jeq check_tip
    ldi ra, $LED_IF
    add rb
    mov rb, acc

check_tip:
    mov ra, m
    ldi rd, $TIP_MASK
    and ra
    mov ra, acc
    cmp zero
    jeq check_busy
    ldi ra, $LED_TIP
    add rb
    mov rb, acc

check_busy:
    mov ra, m
    ldi rd, $BUSY_MASK
    and ra
    mov ra, acc
    cmp zero
    jeq check_al
    ldi ra, $LED_BUSY
    add rb
    mov rb, acc

check_al:
    mov ra, m
    ldi rd, $AL_MASK
    and ra
    mov ra, acc
    cmp zero
    jeq check_rxack
    ldi ra, $LED_AL
    add rb
    mov rb, acc

check_rxack:
    mov ra, m
    ldi rd, $RXACK_MASK
    and ra
    mov ra, acc
    cmp zero
    jeq pack_done
    ldi ra, $LED_RXACK
    add rb
    mov rb, acc

pack_done:
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
