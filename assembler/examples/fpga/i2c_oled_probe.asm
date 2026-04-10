; Minimal I2C address probe for the temporary Gowin I2C wrapper.
; Default target: common 0.96" OLED modules at 7-bit address 0x3C.
;
; Result:
; - ACK received -> SYS LED bit0 = 1
; - No ACK       -> SYS LED bit0 = 0
;
; Change SLAVE_ADDR_W for another device:
; - OLED SSD1306 (0x3C)    -> 0x78
; - LCD1602 PCF8574 (0x27) -> 0x4E
; - LCD1602 PCF8574A(0x3F) -> 0x7E

equ SYS_LED_H        0x0C
equ SYS_LED_L        0x00
equ LED0_MASK        0x01

equ I2C_BASE_H       0x0A
equ I2C_PRESCALE_LO  0x00
equ I2C_PRESCALE_HI  0x01
equ I2C_CONTROL      0x02
equ I2C_TXR          0x03
equ I2C_CR_SR        0x04

equ PRESCALE_100KHZ  0x35 ; 27 MHz / (5 * 100 kHz) - 1 = 53
equ SLAVE_ADDR_W     0x78 ; OLED 7-bit 0x3C with write bit
equ CMD_STOP         0x40
equ CMD_START_WRITE  0x90
equ TIP_MASK         0x02
equ ACK_MASK         0x80

setup:
    mov prh, zero
    mov prl, zero
    mov marl, zero
    mov marh, zero

    ; Clear debug LED before the probe.
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    mov m, zero

    ; All I2C MMIO accesses live at 0x0Axx.
    ldi $I2C_BASE_H
    mov marh, ra

    ; Set prescaler for ~100 kHz SCL.
    ldi $I2C_PRESCALE_LO
    mov marl, ra
    ldi $PRESCALE_100KHZ
    mov m, ra

    ldi $I2C_PRESCALE_HI
    mov marl, ra
    mov m, zero

    ; CONTROL = 0x80 -> enable master, interrupt disabled.
    ldi $I2C_CONTROL
    mov marl, ra
    ldi $ACK_MASK
    mov m, ra

    ; TXR = slave address + write bit.
    ldi $I2C_TXR
    mov marl, ra
    ldi $SLAVE_ADDR_W
    mov m, ra

    ; CR = 0x90 -> START + WRITE.
    ldi $I2C_CR_SR
    mov marl, ra
    ldi $CMD_START_WRITE
    mov m, ra

wait_tip_clear:
    ; Poll SR.TIP until it becomes 0.
    ldi $I2C_CR_SR
    mov marl, ra
    mov rd, m

    ldi $TIP_MASK
    and ra
    mov rd, acc
    cmp zero
    jne wait_tip_clear

    ; Read status again and test RX_ACK (bit7).
    ldi $I2C_CR_SR
    mov marl, ra
    mov rd, m

    ldi $ACK_MASK
    and ra
    mov rd, acc
    cmp zero
    jeq ack_ok

ack_fail:
    ; Optional STOP command even on NACK.
    ldi $I2C_CR_SR
    mov marl, ra
    ldi $CMD_STOP
    mov m, ra

    ; LED off.
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    mov m, zero
    jmpa done

ack_ok:
    ; Issue STOP.
    ldi $I2C_BASE_H
    mov marh, ra
    ldi $I2C_CR_SR
    mov marl, ra
    ldi $CMD_STOP
    mov m, ra

    ; LED on.
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    ldi $LED0_MASK
    mov m, ra

done:
    jmpa done
