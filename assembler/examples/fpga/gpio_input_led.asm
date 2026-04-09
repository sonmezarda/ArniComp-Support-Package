; Poll GPIO bit 0 (MMIO 0x0810) and mirror it to GPIO LED bit 0 (MMIO 0x0C00).
; When gpio[0] is high, LED0 turns on. Otherwise it turns off.

equ GPIO_BASE_H      0x08
equ GPIO0_BIT0_IN_L  0x10
equ SYS_LED_H        0x0C
equ SYS_LED_L        0x00
equ LED0_MASK        0x01

start:
    CLR RA
    CLR PRL
    CLR PRH
    CLR MARL
    CLR MARH

main_loop:
    ; Read GPIO bit-alias register at 0x0810.
    LDI $GPIO_BASE_H
    MOV MARH, RA
    LDI $GPIO0_BIT0_IN_L
    MOV MARL, RA
    MOV RD, M

    ; Compare against 1. If not equal, clear LED0.
    LDI $LED0_MASK
    CMP RA
    JNE led_off

led_on:
    LDI $SYS_LED_H
    MOV MARH, RA
    LDI $SYS_LED_L
    MOV MARL, RA
    LDI $LED0_MASK
    MOV M, RA
    JMPA main_loop

led_off:
    LDI $SYS_LED_H
    MOV MARH, RA
    LDI $SYS_LED_L
    MOV MARL, RA
    CLR RA
    MOV M, RA
    JMPA main_loop
