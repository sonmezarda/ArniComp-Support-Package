; 1 kHz PWM sweep demo
;
; Drives gpio[1] with a 1 kHz PWM waveform.
; Duty sweeps in software from 0x000 -> 0xFFF -> 0x000 repeatedly.
;
; Notes:
; - PWM carrier stays at 1 kHz in hardware.
; - Sweep speed depends on CPU clock, because duty updates are done in software.
; - RD stores duty low byte, RB stores the upper 4 bits in its low nibble.

equ GPIO_BASE_H          0x08

equ GPIO0_PWM_PERIOD_LO  0x08
equ GPIO0_PWM_PERIOD_MI  0x09
equ GPIO0_PWM_PERIOD_HI  0x0A

equ GPIO_BIT1_OUT_L      0x21
equ GPIO_BIT1_DIR_L      0x31
equ GPIO_BIT1_PWM_EN_L   0x41
equ GPIO_BIT1_DUTY_LO    0x52
equ GPIO_BIT1_DUTY_HI    0x53

equ PWM_PERIOD_LO        0x77    ; 26999 = 0x006977
equ PWM_PERIOD_MI        0x69
equ PWM_PERIOD_HI        0x00
equ DUTY_HI_MAX          0x0F

start:
    CLR RA
    CLR PRL
    CLR PRH
    CLR MARL
    CLR MARH

    LDI $GPIO_BASE_H
    MOV MARH, RA

    ; GPIO0 period = 1 kHz at 27 MHz pwm clock.
    LDI $GPIO0_PWM_PERIOD_LO
    MOV MARL, RA
    LDI $PWM_PERIOD_LO
    MOV M, RA

    LDI $GPIO0_PWM_PERIOD_MI
    MOV MARL, RA
    LDI $PWM_PERIOD_MI
    MOV M, RA

    LDI $GPIO0_PWM_PERIOD_HI
    MOV MARL, RA
    LDI $PWM_PERIOD_HI
    MOV M, RA

    ; Set gpio[1] direction = output.
    LDI $GPIO_BIT1_DIR_L
    MOV MARL, RA
    LDI #1
    MOV M, RA

    ; Preload normal GPIO output low.
    LDI $GPIO_BIT1_OUT_L
    MOV MARL, RA
    CLR RA
    MOV M, RA

    ; Enable PWM on gpio[1].
    LDI $GPIO_BIT1_PWM_EN_L
    MOV MARL, RA
    LDI #1
    MOV M, RA

    ; Keep MARL parked on the duty low-byte register during the sweep loop.
    LDI $GPIO_BIT1_DUTY_LO
    MOV MARL, RA

    ; Start at duty = 0x000.
    CLR RA
    MOV RD, RA
    MOV RB, RA

ramp_up:
    ; Write current duty to gpio[1].
    MOV RA, RD
    MOV M, RA

    INC #1
    MOV RA, RB
    MOV M, RA
    DEC #1

    ; If low byte != 0xFF, just increment low byte.
    CLR RA
    NOT RA
    MOV RA, ACC
    CMP RA
    JNE inc_low

    ; Low byte is 0xFF. If high nibble == 0x0F, reverse direction.
    MOV RD, RB
    LDI $DUTY_HI_MAX
    CMP RA
    JEQ prep_ramp_down

    ; Otherwise increment high nibble and wrap low byte to 0x00.
    ADDI #1
    MOV RB, ACC
    CLR RA
    MOV RD, RA
    JMPA ramp_up

inc_low:
    ADDI #1
    MOV RD, ACC
    JMPA ramp_up

prep_ramp_down:
    CLR RA
    NOT RA
    MOV RD, ACC
    LDI $DUTY_HI_MAX
    MOV RB, RA
    JMPA ramp_down

ramp_down:
    ; Write current duty to gpio[1].
    MOV RA, RD
    MOV M, RA

    INC #1
    MOV RA, RB
    MOV M, RA
    DEC #1

    ; If low byte != 0x00, decrement low byte.
    CLR RA
    CMP RA
    JEQ low_zero
    SUBI #1
    MOV RD, ACC
    JMPA ramp_down

low_zero:
    ; If high nibble is also zero, reverse direction.
    MOV RD, RB
    CLR RA
    CMP RA
    JEQ prep_ramp_up

    ; Otherwise decrement high nibble and set low byte to 0xFF.
    SUBI #1
    MOV RB, ACC
    CLR RA
    NOT RA
    MOV RD, ACC
    JMPA ramp_down

prep_ramp_up:
    CLR RD
    CLR RB
    JMPA ramp_up
