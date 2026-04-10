; One-shot I2C status snapshot for the temporary Gowin I2C wrapper.
;
; This program performs exactly one START+WRITE address phase, captures the
; resulting status, maps key flags onto the 6 on-board LEDs, then stops there.
;
; LED mapping written into SYS_LED[5:0]:
; - bit0 -> raw INT register bit0
; - bit1 -> status IF
; - bit2 -> status TIP
; - bit3 -> status BUSY
; - bit4 -> status AL
; - bit5 -> status RX_ACK (1 = NACK, 0 = ACK)
;
; Expected interpretation:
; - OLED disconnected: bit5 should usually be 1
; - OLED connected at correct address: bit5 should become 0

equ SYS_LED_H        0x0C
equ SYS_LED_L        0x00

equ I2C_BASE_H       0x0A
equ I2C_PRESCALE_LO  0x00
equ I2C_PRESCALE_HI  0x01
equ I2C_CONTROL      0x02
equ I2C_TXR          0x03
equ I2C_CR_SR        0x04
equ I2C_INT          0x05

equ PRESCALE_DEBUG   0x00
equ SLAVE_ADDR_W     0x78

equ CTRL_ENABLE      0x80
equ CMD_START_WRITE  0x90
equ CMD_STOP         0x40

equ IF_MASK          0x01
equ TIP_MASK         0x02
equ BUSY_MASK        0x40
equ AL_MASK          0x20
equ RXACK_MASK       0x80

equ LED_INT          0x01
equ LED_IF           0x02
equ LED_TIP          0x04
equ LED_BUSY         0x08
equ LED_AL           0x10
equ LED_RXACK        0x20

equ TIMEOUT_COUNT    100

setup:
    mov prh, zero
    mov prl, zero
    mov marl, zero
    mov marh, zero
    mov rb, zero

    ; Clear LEDs.
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    mov m, zero

    ; Point to I2C MMIO page.
    ldi $I2C_BASE_H
    mov marh, ra

    ; Minimal prescale for visible activity on a slow cpu_clk-driven core.
    ldi $I2C_PRESCALE_LO
    mov marl, ra
    ldi $PRESCALE_DEBUG
    mov m, ra

    ldi $I2C_PRESCALE_HI
    mov marl, ra
    mov m, zero

    ; Enable master.
    ldi $I2C_CONTROL
    mov marl, ra
    ldi $CTRL_ENABLE
    mov m, ra

    ; Load address + write bit.
    ldi $I2C_TXR
    mov marl, ra
    ldi $SLAVE_ADDR_W
    mov m, ra

    ; Launch START + WRITE.
    ldi $I2C_CR_SR
    mov marl, ra
    ldi $CMD_START_WRITE
    mov m, ra

    ; Wait until TIP clears or timeout expires.
    ldi rd, $TIMEOUT_COUNT

wait_tip_low:
    ldi $I2C_BASE_H
    mov marh, ra
    ldi $I2C_CR_SR
    mov marl, ra
    mov ra, m

    ldi rd, $TIP_MASK
    and ra
    mov rd, acc
    cmp zero
    jeq capture_status

    subi #1
    mov rd, acc
    jeq capture_status
    jmp wait_tip_low

capture_status:
    mov rb, zero

    ; Read raw INT flag.
    ldi $I2C_BASE_H
    mov marh, ra
    ldi $I2C_INT
    mov marl, ra
    mov ra, m

    ldi rd, $IF_MASK
    and ra
    mov rd, acc
    cmp zero
    jeq read_status_reg

    ldi rd, $LED_INT
    add rb
    mov rb, acc

read_status_reg:
    ; Read status and keep a stable copy in RA.
    ldi $I2C_BASE_H
    mov marh, ra
    ldi $I2C_CR_SR
    mov marl, ra
    mov ra, m

check_if:
    ldi rd, $IF_MASK
    and ra
    mov rd, acc
    cmp zero
    jeq check_tip
    ldi rd, $LED_IF
    add rb
    mov rb, acc

check_tip:
    ldi rd, $TIP_MASK
    and ra
    mov rd, acc
    cmp zero
    jeq check_busy
    ldi rd, $LED_TIP
    add rb
    mov rb, acc

check_busy:
    ldi rd, $BUSY_MASK
    and ra
    mov rd, acc
    cmp zero
    jeq check_al
    ldi rd, $LED_BUSY
    add rb
    mov rb, acc

check_al:
    ldi rd, $AL_MASK
    and ra
    mov rd, acc
    cmp zero
    jeq check_rxack
    ldi rd, $LED_AL
    add rb
    mov rb, acc

check_rxack:
    ldi rd, $RXACK_MASK
    and ra
    mov rd, acc
    cmp zero
    jeq issue_stop
    ldi rd, $LED_RXACK
    add rb
    mov rb, acc

issue_stop:
    ldi $I2C_BASE_H
    mov marh, ra
    ldi $I2C_CR_SR
    mov marl, ra
    ldi $CMD_STOP
    mov m, ra

    ; Show the captured snapshot and stop changing state.
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    mov m, rb

done:
    jmpa done
