; Raw I2C status dump.
;
; This program performs one START+WRITE address phase, waits a while,
; then writes the raw Gowin I2C status register byte directly to SYS_LED.
;
; On Tang Nano 9K only the lower 6 bits are visible on LEDs, so you will see:
; - led[0] <- status bit0 (IF)
; - led[1] <- status bit1 (TIP)
; - led[2] <- status bit2
; - led[3] <- status bit3
; - led[4] <- status bit4 (AL)
; - led[5] <- status bit5 (BUSY)
;
; Status bit7 (RX_ACK) is not directly visible with only 6 LEDs.

equ SYS_LED_H        0x0C
equ SYS_LED_L        0x00

equ I2C_BASE_H       0x0A
equ I2C_PRESCALE_LO  0x00
equ I2C_PRESCALE_HI  0x01
equ I2C_CONTROL      0x02
equ I2C_TXR          0x03
equ I2C_CR_SR        0x04

equ PRESCALE_DEBUG   0x00
equ SLAVE_ADDR_W     0x78
equ CTRL_ENABLE      0x80
equ CMD_START_WRITE  0x90
equ CMD_STOP         0x40
equ WAIT_COUNT       120

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
    ldi $PRESCALE_DEBUG
    mov m, ra

    ldi $I2C_PRESCALE_HI
    mov marl, ra
    mov m, zero

    ldi $I2C_CONTROL
    mov marl, ra
    ldi $CTRL_ENABLE
    mov m, ra

    ldi $I2C_TXR
    mov marl, ra
    ldi $SLAVE_ADDR_W
    mov m, ra

    ldi $I2C_CR_SR
    mov marl, ra
    ldi $CMD_START_WRITE
    mov m, ra

    ldi rd, $WAIT_COUNT

wait_loop:
    subi #1
    mov rd, acc
    jne wait_loop

    ldi $I2C_BASE_H
    mov marh, ra
    ldi $I2C_CR_SR
    mov marl, ra
    mov rb, m

    ldi $I2C_CR_SR
    mov marl, ra
    ldi $CMD_STOP
    mov m, ra

    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    mov m, rb

done:
    jmpa done
