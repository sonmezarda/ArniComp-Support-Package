equ GPIO_BASE_H      0x08
equ GPIO0_BIT0_IN_L  0x10
equ GPIO0_BIT1_OUT_L 0x21
equ GPIO0_DIR1_OUT_L 0x31
equ LED0_MASK        0x01

start:
    CLR RA
    CLR PRL
    CLR PRH
    LDI $GPIO_BASE_H
    MOV MARH, RA

    LDI $GPIO0_DIR1_OUT_L
    MOV MARL, RA

    LDI #1
    MOV M, RA

main_loop:
    ; Read GPIO bit-alias register at 0x0810.
    
    LDI $GPIO0_BIT0_IN_L
    MOV MARL, RA
    MOV RD, M

    ; Compare against 1. If not equal, clear LED0.
    LDI $LED0_MASK
    CMP RA
    JNE led_off

led_on:
    LDI $GPIO0_BIT1_OUT_L
    MOV MARL, RA
    LDI #1
    MOV M, RA
    JMPA main_loop

led_off:
    LDI $GPIO0_BIT1_OUT_L
    MOV MARL, RA
    CLR RA
    MOV M, RA
    JMPA main_loop
