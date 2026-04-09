; Minimal PWM bring-up test - 50 kHz
;
; Drives gpio[1] with a fixed PWM waveform, then halts the CPU so
; only the hardware PWM block remains active.
;
; Current settings:
;   period = 0x021B = 539
;   pwm_clk = 27 MHz
;   pwm_freq = 27_000_000 / (539 + 1) = 50_000 Hz
;   duty = 0x80 = 128 -> about 50%
;
; This is the higher-frequency version. For easier scope bring-up,
; see gpio_pwm_1khz_demo.asm.

equ GPIO_BASE_H         0x08

equ GPIO0_PWM_PERIOD_LO 0x08
equ GPIO0_PWM_PERIOD_MI 0x09
equ GPIO0_PWM_PERIOD_HI 0x0A

equ GPIO_BIT1_OUT_L     0x21
equ GPIO_BIT1_DIR_L     0x31
equ GPIO_BIT1_PWM_EN_L  0x41
equ GPIO_BIT1_DUTY_LO   0x52
equ GPIO_BIT1_DUTY_HI   0x53

equ PWM_PERIOD_LO       0x1B    ; 539 = 0x00021B
equ PWM_PERIOD_MI       0x02
equ PWM_PERIOD_HI       0x00
equ DUTY_50_LO          0x00
equ DUTY_50_HI          0x08    ; 0x800 -> about 50%

start:
    CLR RA
    CLR PRL
    CLR PRH
    CLR MARL
    CLR MARH

    ; All GPIO MMIO accesses are under 0x08xx.
    LDI $GPIO_BASE_H
    MOV MARH, RA

    ; GPIO0 period low byte.
    LDI $GPIO0_PWM_PERIOD_LO
    MOV MARL, RA
    LDI $PWM_PERIOD_LO
    MOV M, RA

    ; GPIO0 period middle byte.
    LDI $GPIO0_PWM_PERIOD_MI
    MOV MARL, RA
    LDI $PWM_PERIOD_MI
    MOV M, RA

    ; GPIO0 period high byte.
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

    ; Duty = 0x800 -> about 50%.
    LDI $GPIO_BIT1_DUTY_LO
    MOV MARL, RA
    LDI $DUTY_50_LO
    MOV M, RA

    INC #1
    LDI $DUTY_50_HI
    MOV M, RA

    ; Enable PWM on gpio[1].
    LDI $GPIO_BIT1_PWM_EN_L
    MOV MARL, RA
    LDI #1
    MOV M, RA

    HLT
    HLT
