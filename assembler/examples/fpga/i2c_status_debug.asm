; I2C status-oriented debug program for the temporary Gowin I2C wrapper.
;
; Important:
; - In the current FPGA build, the Gowin I2C IP is clocked from cpu_clk,
;   not directly from the 27 MHz board clock.
; - Use the minimum prescale here so any bus activity is easy to catch on a scope.
;
; LED meanings:
; - 0x01: setup complete
; - 0x02: command written
; - 0x04: TIP observed high at least once
; - 0x08: TIP never went high before timeout
; - 0x10: transfer ended with NACK
; - 0x20: transfer ended with ACK
;
; Change SLAVE_ADDR_W if you want to probe another device:
; - OLED SSD1306 (0x3C)    -> 0x78
; - LCD1602 PCF8574 (0x27) -> 0x4E
; - LCD1602 PCF8574A(0x3F) -> 0x7E

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

equ TIP_MASK         0x02
equ ACK_MASK         0x80

equ LED_SETUP        0x01
equ LED_CMD_WRITTEN  0x02
equ LED_TIP_SEEN     0x04
equ LED_TIP_TIMEOUT  0x08
equ LED_NACK         0x10
equ LED_ACK          0x20

equ TIMEOUT_COUNT    100

setup:
    mov prh, zero
    mov prl, zero
    mov marl, zero
    mov marh, zero

    ; Clear LEDs.
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    mov m, zero

    ; Point MARH at the I2C MMIO page.
    ldi $I2C_BASE_H
    mov marh, ra

    ; Use the minimum prescale so SCL toggles as fast as possible with cpu_clk.
    ldi $I2C_PRESCALE_LO
    mov marl, ra
    ldi $PRESCALE_DEBUG
    mov m, ra

    ldi $I2C_PRESCALE_HI
    mov marl, ra
    mov m, zero

    ; Enable I2C master.
    ldi $I2C_CONTROL
    mov marl, ra
    ldi $CTRL_ENABLE
    mov m, ra

    ; Show setup complete.
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    ldi $LED_SETUP
    mov m, ra

main_loop:
    ; Restore I2C MMIO page after LED writes.
    ldi $I2C_BASE_H
    mov marh, ra

    ; Load transmit register with slave address + write bit.
    ldi $I2C_TXR
    mov marl, ra
    ldi $SLAVE_ADDR_W
    mov m, ra

    ; Launch START + WRITE.
    ldi $I2C_CR_SR
    mov marl, ra
    ldi $CMD_START_WRITE
    mov m, ra

    ; Show that the command byte was written.
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    ldi $LED_CMD_WRITTEN
    mov m, ra

    ; Wait for TIP to become 1 at least once.
    ldi rd, $TIMEOUT_COUNT

wait_tip_high:
    ldi $I2C_BASE_H
    mov marh, ra
    ldi $I2C_CR_SR
    mov marl, ra
    mov rd, m

    ldi $TIP_MASK
    and ra
    mov rd, acc
    cmp zero
    jne tip_went_high

    subi #1
    mov rd, acc
    jeq tip_timeout
    jmp wait_tip_high

tip_went_high:
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    ldi $LED_TIP_SEEN
    mov m, ra

wait_tip_low:
    ldi $I2C_BASE_H
    mov marh, ra
    ldi $I2C_CR_SR
    mov marl, ra
    mov rd, m

    ldi $TIP_MASK
    and ra
    mov rd, acc
    cmp zero
    jeq check_ack
    jmp wait_tip_low

check_ack:
    ldi $I2C_BASE_H
    mov marh, ra
    ldi $I2C_CR_SR
    mov marl, ra
    mov rd, m

    ldi $ACK_MASK
    and ra
    mov rd, acc
    cmp zero
    jeq ack_ok

nack_seen:
    ; Stop and show NACK.
    ldi $I2C_BASE_H
    mov marh, ra
    ldi $I2C_CR_SR
    mov marl, ra
    ldi $CMD_STOP
    mov m, ra

    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    ldi $LED_NACK
    mov m, ra
    jmpa main_loop

ack_ok:
    ; Stop and show ACK.
    ldi $I2C_BASE_H
    mov marh, ra
    ldi $I2C_CR_SR
    mov marl, ra
    ldi $CMD_STOP
    mov m, ra

    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    ldi $LED_ACK
    mov m, ra
    jmpa main_loop

tip_timeout:
    ; The command never appeared active.
    ldi $I2C_BASE_H
    mov marh, ra
    ldi $I2C_CR_SR
    mov marl, ra
    ldi $CMD_STOP
    mov m, ra

    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    ldi $LED_TIP_TIMEOUT
    mov m, ra
    jmpa main_loop
