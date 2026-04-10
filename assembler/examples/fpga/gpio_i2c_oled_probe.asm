; Software I2C ACK probe on verified GPIO pins.
;
; Wiring for this test:
; - gpio[0] / physical pin 25 -> SCL
; - gpio[1] / physical pin 26 -> SDA
;
; Open-drain emulation:
; - output register bit is kept at 0
; - DIR=1 drives low
; - DIR=0 releases the line high through the pull-up already present on the OLED board
;
; Visible LED result on Tang Nano 9K:
; - only LED0 on -> ACK
; - only LED1 on -> NACK

equ GPIO_BASE_H       0x08
equ GPIO_IN0_L        0x10
equ GPIO_IN1_L        0x11
equ GPIO_OUT0_L       0x20
equ GPIO_OUT1_L       0x21
equ GPIO_DIR0_L       0x30
equ GPIO_DIR1_L       0x31

equ SYS_LED_H         0x0C
equ SYS_LED_L         0x00
equ LED_ACK           0x01
equ LED_NACK          0x02

equ SCL_RELEASE       0x00
equ SCL_DRIVE_LOW     0x01
equ SDA_RELEASE       0x00
equ SDA_DRIVE_LOW     0x01

equ ACK_EXPECTED      0x00
equ DELAY_COUNT       8

setup:
    mov prh, zero
    mov prl, zero
    mov marl, zero
    mov marh, zero

    ; Clear visible LEDs.
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    mov m, zero

    ; Put GPIO0/1 output data to 0 so DIR alone controls open-drain behavior.
    ldi $GPIO_BASE_H
    mov marh, ra

    ldi $GPIO_OUT0_L
    mov marl, ra
    mov m, zero

    ldi $GPIO_OUT1_L
    mov marl, ra
    mov m, zero

    ; Release both lines high.
    ldi $GPIO_DIR0_L
    mov marl, ra
    mov m, zero

    ldi $GPIO_DIR1_L
    mov marl, ra
    mov m, zero

    call delay_short

    ; START: SDA low while SCL high.
    ldi $GPIO_DIR1_L
    mov marl, ra
    ldi $SDA_DRIVE_LOW
    mov m, ra
    call delay_short

    ; Pull SCL low to start clocking.
    ldi $GPIO_DIR0_L
    mov marl, ra
    ldi $SCL_DRIVE_LOW
    mov m, ra
    call delay_short

    ; Send 0x78 = 0b01111000
    ; Bit 7 = 0
    ldi $GPIO_BASE_H
    mov marh, ra
    ldi $GPIO_DIR1_L
    mov marl, ra
    ldi $SDA_DRIVE_LOW
    mov m, ra
    call delay_short
    ldi $GPIO_DIR0_L
    mov marl, ra
    ldi $SCL_RELEASE
    mov m, ra
    call delay_short
    ldi $GPIO_DIR0_L
    mov marl, ra
    ldi $SCL_DRIVE_LOW
    mov m, ra
    call delay_short

    ; Bit 6 = 1
    ldi $GPIO_BASE_H
    mov marh, ra
    ldi $GPIO_DIR1_L
    mov marl, ra
    ldi $SDA_RELEASE
    mov m, ra
    call delay_short
    ldi $GPIO_DIR0_L
    mov marl, ra
    ldi $SCL_RELEASE
    mov m, ra
    call delay_short
    ldi $GPIO_DIR0_L
    mov marl, ra
    ldi $SCL_DRIVE_LOW
    mov m, ra
    call delay_short

    ; Bit 5 = 1
    ldi $GPIO_BASE_H
    mov marh, ra
    ldi $GPIO_DIR1_L
    mov marl, ra
    ldi $SDA_RELEASE
    mov m, ra
    call delay_short
    ldi $GPIO_DIR0_L
    mov marl, ra
    ldi $SCL_RELEASE
    mov m, ra
    call delay_short
    ldi $GPIO_DIR0_L
    mov marl, ra
    ldi $SCL_DRIVE_LOW
    mov m, ra
    call delay_short

    ; Bit 4 = 1
    ldi $GPIO_BASE_H
    mov marh, ra
    ldi $GPIO_DIR1_L
    mov marl, ra
    ldi $SDA_RELEASE
    mov m, ra
    call delay_short
    ldi $GPIO_DIR0_L
    mov marl, ra
    ldi $SCL_RELEASE
    mov m, ra
    call delay_short
    ldi $GPIO_DIR0_L
    mov marl, ra
    ldi $SCL_DRIVE_LOW
    mov m, ra
    call delay_short

    ; Bit 3 = 1
    ldi $GPIO_BASE_H
    mov marh, ra
    ldi $GPIO_DIR1_L
    mov marl, ra
    ldi $SDA_RELEASE
    mov m, ra
    call delay_short
    ldi $GPIO_DIR0_L
    mov marl, ra
    ldi $SCL_RELEASE
    mov m, ra
    call delay_short
    ldi $GPIO_DIR0_L
    mov marl, ra
    ldi $SCL_DRIVE_LOW
    mov m, ra
    call delay_short

    ; Bit 2 = 0
    ldi $GPIO_BASE_H
    mov marh, ra
    ldi $GPIO_DIR1_L
    mov marl, ra
    ldi $SDA_DRIVE_LOW
    mov m, ra
    call delay_short
    ldi $GPIO_DIR0_L
    mov marl, ra
    ldi $SCL_RELEASE
    mov m, ra
    call delay_short
    ldi $GPIO_DIR0_L
    mov marl, ra
    ldi $SCL_DRIVE_LOW
    mov m, ra
    call delay_short

    ; Bit 1 = 0
    ldi $GPIO_BASE_H
    mov marh, ra
    ldi $GPIO_DIR1_L
    mov marl, ra
    ldi $SDA_DRIVE_LOW
    mov m, ra
    call delay_short
    ldi $GPIO_DIR0_L
    mov marl, ra
    ldi $SCL_RELEASE
    mov m, ra
    call delay_short
    ldi $GPIO_DIR0_L
    mov marl, ra
    ldi $SCL_DRIVE_LOW
    mov m, ra
    call delay_short

    ; Bit 0 = 0
    ldi $GPIO_BASE_H
    mov marh, ra
    ldi $GPIO_DIR1_L
    mov marl, ra
    ldi $SDA_DRIVE_LOW
    mov m, ra
    call delay_short
    ldi $GPIO_DIR0_L
    mov marl, ra
    ldi $SCL_RELEASE
    mov m, ra
    call delay_short
    ldi $GPIO_DIR0_L
    mov marl, ra
    ldi $SCL_DRIVE_LOW
    mov m, ra
    call delay_short

    ; ACK bit: release SDA and sample while SCL is high.
    ldi $GPIO_DIR1_L
    mov marl, ra
    ldi $SDA_RELEASE
    mov m, ra
    call delay_short

    ldi $GPIO_DIR0_L
    mov marl, ra
    ldi $SCL_RELEASE
    mov m, ra
    call delay_short

    ldi $GPIO_IN1_L
    mov marl, ra
    mov rd, m
    mov rb, rd

    ; Finish ACK clock.
    ldi $GPIO_DIR0_L
    mov marl, ra
    ldi $SCL_DRIVE_LOW
    mov m, ra
    call delay_short

    ; STOP: SDA low while SCL low, then release SCL, then release SDA.
    ldi $GPIO_DIR1_L
    mov marl, ra
    ldi $SDA_DRIVE_LOW
    mov m, ra
    call delay_short

    ldi $GPIO_DIR0_L
    mov marl, ra
    ldi $SCL_RELEASE
    mov m, ra
    call delay_short

    ldi $GPIO_DIR1_L
    mov marl, ra
    ldi $SDA_RELEASE
    mov m, ra
    call delay_short

    ; Show result.
    ldi $ACK_EXPECTED
    cmp rb
    jeq show_ack

show_nack:
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    ldi $LED_NACK
    mov m, ra
    jmpa done

show_ack:
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    ldi $LED_ACK
    mov m, ra
    jmpa done

delay_short:
    ldi rd, $DELAY_COUNT

delay_loop:
    subi #1
    mov rd, acc
    jne delay_loop
    ret

done:
    jmpa done
