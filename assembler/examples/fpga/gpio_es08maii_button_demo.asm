; ES08MA II servo demo using GPIO PWM
;
; gpio[1] -> servo signal output
; gpio[0] -> button input
;
; Behavior:
; - button not pressed (gpio[0] = 0): servo goes to minimum position
; - button pressed     (gpio[0] = 1): servo goes to maximum position
;
; Assumptions:
; - pwm_clk = 27 MHz
; - ES08MA II-style frame rate = 50 Hz (20 ms)
; - published control data indicates:
;   - about 95 deg total travel for 1000..2000 us
;   - about 170 deg total travel for 600..2400 us
; - the "1500 to 1900 us" text seen on some store pages appears to describe
;   pulse travel direction around neutral, not the full command range
; - this demo maps:
;   - button released -> minimum pulse ~= 600 us
;   - button pressed  -> maximum pulse ~= 2400 us
;
; PWM hardware uses:
;   duty_12b ~= pulse_width / frame_period * 4096
;
; With period = 539999 counts (20 ms at 27 MHz):
; - 0.6 ms  -> about 123  = 0x07B
; - 2.4 ms  -> about 492  = 0x1EC

equ GPIO_BASE_H          0x08

equ GPIO0_PWM_PERIOD_LO  0x08
equ GPIO0_PWM_PERIOD_MI  0x09
equ GPIO0_PWM_PERIOD_HI  0x0A

equ GPIO_BIT0_IN_L       0x10
equ GPIO_BIT1_OUT_L      0x21
equ GPIO_BIT1_DIR_L      0x31
equ GPIO_BIT1_PWM_EN_L   0x41
equ GPIO_BIT1_DUTY_LO    0x52
equ GPIO_BIT1_DUTY_HI    0x53

equ PWM_PERIOD_LO        0x5F    ; 539999 = 0x083D5F
equ PWM_PERIOD_MI        0x3D
equ PWM_PERIOD_HI        0x08

equ SERVO_MIN_LO         0x7B    ; 0x07B ~= 0.6 ms
equ SERVO_MIN_HI         0x00
equ SERVO_MAX_LO         0xEC    ; 0x1EC ~= 2.4 ms
equ SERVO_MAX_HI         0x01

start:
    CLR RA
    CLR PRL
    CLR PRH
    CLR MARL
    CLR MARH

    LDI $GPIO_BASE_H
    MOV MARH, RA

    ; GPIO0 period = 50 Hz at 27 MHz pwm clock.
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

main_loop:
    ; Read button from gpio[0].
    LDI $GPIO_BIT0_IN_L
    MOV MARL, RA
    MOV RD, M

    ; If gpio[0] == 1, select the maximum position.
    LDI #1
    CMP RA
    JEQ set_90

set_0:
    LDI $GPIO_BIT1_DUTY_LO
    MOV MARL, RA
    LDI $SERVO_MIN_LO
    MOV M, RA
    INC #1
    LDI $SERVO_MIN_HI
    MOV M, RA
    JMPA main_loop

set_90:
    LDI $GPIO_BIT1_DUTY_LO
    MOV MARL, RA
    LDI $SERVO_MAX_LO
    MOV M, RA
    INC #1
    LDI $SERVO_MAX_HI
    MOV M, RA
    JMPA main_loop
