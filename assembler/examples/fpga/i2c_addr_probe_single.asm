; Single-transaction Gowin-I2C address probe.
;
; This test sends exactly one byte on the bus:
;   START + slave_address(write) + STOP
;
; Why this test exists:
; Previous address-only tests used START+WRITE first and STOP later.
; According to the Gowin I2C status definition, AL is also set when a STOP
; condition is detected without having been requested. That can make a naive
; address-only probe look like arbitration loss even if the bus wiring is fine.
;
; Board assumptions:
; - Tang Nano 9K top uses the direct 27 MHz crystal as cpu_clk
; - Gowin I2C IP is routed to PMOD pin 25 = SCL, pin 26 = SDA
;
; LED result:
; - 0x01 -> ACK received
; - 0x02 -> NACK received
; - 0x04 -> AL set
; - 0x08 -> timeout waiting for IF

equ SYS_LED_H            0x0C
equ SYS_LED_L            0x00

equ I2C_BASE_H           0x0A
equ I2C_PRESCALE_LO      0x00
equ I2C_PRESCALE_HI      0x01
equ I2C_CONTROL          0x02
equ I2C_TXR              0x03
equ I2C_CR_SR            0x04

equ PRESCALE_100KHZ      0x35
equ SLAVE_ADDR_W         0x78
equ CTRL_ENABLE          0x80
equ CMD_STA_WR_STO       0xD0

equ IF_MASK              0x01
equ AL_MASK              0x20
equ RXACK_MASK           0x80

equ LED_ACK              0x01
equ LED_NACK             0x02
equ LED_AL               0x04
equ LED_TIMEOUT          0x08

equ WAIT_COUNT           200

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

    ldi $I2C_TXR
    mov marl, ra
    ldi $SLAVE_ADDR_W
    mov m, ra

    ; START + WRITE + STOP in a single command.
    ldi $I2C_CR_SR
    mov marl, ra
    ldi $CMD_STA_WR_STO
    mov m, ra

    ldi rd, $WAIT_COUNT

wait_if:
    ldi $I2C_BASE_H
    mov marh, ra
    ldi $I2C_CR_SR
    mov marl, ra
    mov ra, m

    ldi rd, $IF_MASK
    and ra
    mov rd, acc
    cmp zero
    jne read_final_status

    subi #1
    mov rd, acc
    jeq timeout
    jmp wait_if

read_final_status:
    ldi $I2C_BASE_H
    mov marh, ra
    ldi $I2C_CR_SR
    mov marl, ra
    mov rb, m

    ; Priority 1: explicit arbitration-lost / stop-not-requested condition.
    mov rd, rb
    ldi ra, $AL_MASK
    and ra
    mov rd, acc
    cmp zero
    jne show_al

    ; Priority 2: RX_ACK bit distinguishes ACK vs NACK.
    mov rd, rb
    ldi ra, $RXACK_MASK
    and ra
    mov rd, acc
    cmp zero
    jne show_nack

show_ack:
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    ldi $LED_ACK
    mov m, ra
    jmpa done

show_nack:
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    ldi $LED_NACK
    mov m, ra
    jmpa done

show_al:
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    ldi $LED_AL
    mov m, ra
    jmpa done

timeout:
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    ldi $LED_TIMEOUT
    mov m, ra

done:
    jmpa done
