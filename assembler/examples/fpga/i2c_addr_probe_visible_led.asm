; I2C address probe with LED output corrected for Tang Nano 9K active-low LEDs.
;
; Visible LED meaning on the board:
; - 000001 -> ACK
; - 000010 -> NACK
; - 000100 -> AL
; - 001000 -> timeout
;
; Notes:
; - Tang Nano 9K board LEDs are active-low in the top-level.
; - Therefore this program writes the inverted pattern into SYS_LED so the
;   visible LEDs match the meanings above directly.

equ SYS_LED_H            0x0C
equ SYS_LED_L            0x00

equ I2C_BASE_H           0x0A
equ I2C_PRESCALE_LO      0x00
equ I2C_PRESCALE_HI      0x01
equ I2C_CONTROL          0x02
equ I2C_TXR              0x03
equ I2C_CR_SR            0x04

equ PRESCALE_DEBUG       0x00
equ SLAVE_ADDR_W         0x78
equ CTRL_ENABLE          0x80
equ CMD_STA_WR_STO       0xD0

equ IF_MASK              0x01
equ AL_MASK              0x20
equ RXACK_MASK           0x80

equ LEDV_ACK             0x01
equ LEDV_NACK            0x02
equ LEDV_AL              0x04
equ LEDV_TIMEOUT         0x08

equ WAIT_COUNT           120

setup:
    mov prh, zero
    mov prl, zero
    mov marl, zero
    mov marh, zero

    ; All LEDs off visually.
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    ldi #0x3F
    mov m, ra

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

    mov rd, rb
    ldi ra, $AL_MASK
    and ra
    mov rd, acc
    cmp zero
    jne show_al

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
    ldi $LEDV_ACK
    not ra
    mov m, acc
    jmpa done

show_nack:
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    ldi $LEDV_NACK
    not ra
    mov m, acc
    jmpa done

show_al:
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    ldi $LEDV_AL
    not ra
    mov m, acc
    jmpa done

timeout:
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    ldi $LEDV_TIMEOUT
    not ra
    mov m, acc

done:
    jmpa done
