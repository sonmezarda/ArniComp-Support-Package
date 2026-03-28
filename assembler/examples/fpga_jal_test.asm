equ SYS_LED_H 0x0C
equ SYS_LED_L 0x00

equ CLOCK_HZ 10000
equ LINK_RET_L 0x10
equ LINK_RET_H 0x11
equ DELAY_SLOT 0x12

equ BLINK_DELAY_MS 100
equ LED_ON_VALUE 0x3F
equ LED_OFF_VALUE 0x00
equ DELAY_TARGET_CYCLES (CLOCK_HZ / 1000)
equ DELAY_INNER_COUNT MAX(1, MIN(127, ((DELAY_TARGET_CYCLES - 41) / 14)))
equ DELAY_MID_BLOCK_CYCLES (18 + (14 * DELAY_INNER_COUNT))
equ DELAY_MID_COUNT MAX(1, (((DELAY_TARGET_CYCLES - 23) + (DELAY_MID_BLOCK_CYCLES / 2)) / DELAY_MID_BLOCK_CYCLES))

; Software JAL convention for this ISA:
; 1. Caller writes return label low/high to LINK_RET_L / LINK_RET_H
; 2. Caller puts delay parameter in RB
; 3. Caller jumps to delay
; 4. delay returns by restoring PRL/PRH from the link slots
;
; Delay calibration:
; One outer iteration is approximately:
;   23 + DELAY_MID_COUNT * (18 + 14 * DELAY_INNER_COUNT) cycles
; DELAY_MID_COUNT is derived from CLOCK_HZ, so changing CLOCK_HZ
; updates the compiled loop count automatically.
; DELAY_INNER_COUNT is also derived from CLOCK_HZ so low clock values
; do not get stuck with an oversized minimum delay block.
;
; Tang Nano top currently divides 27 MHz down to a 500 kHz CPU clock,
; so CLOCK_HZ defaults to 500000 here.
;
; LED outputs are active-low in hardware (led = ~debug_led[5:0]).
; Writing 0x3F turns all 6 onboard LEDs on, writing 0x00 turns them off.

; ---- reset / init ----
ldi #0
mov prh, ra
mov prl, ra
mov marh, ra
mov marl, ra

main_loop:
    ; LED ON
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    ldi $LED_ON_VALUE
    mov m, ra

    ; call delay(BLINK_DELAY_MS)
    ldi #0
    mov marh, ra
    ldi $LINK_RET_L
    mov marl, ra
    ldi @after_on_delay.low
    mov m, ra
    ldi $LINK_RET_H
    mov marl, ra
    ldi @after_on_delay.high
    mov m, ra
    ldi $BLINK_DELAY_MS
    mov rb, ra
    ldi @delay.low
    mov prl, ra
    ldi @delay.high
    mov prh, ra
    jmp

after_on_delay:
    ; LED OFF
    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    ldi $LED_OFF_VALUE
    mov m, ra

    ; call delay(BLINK_DELAY_MS)
    ldi #0
    mov marh, ra
    ldi $LINK_RET_L
    mov marl, ra
    ldi @after_off_delay.low
    mov m, ra
    ldi $LINK_RET_H
    mov marl, ra
    ldi @after_off_delay.high
    mov m, ra
    ldi $BLINK_DELAY_MS
    mov rb, ra
    ldi @delay.low
    mov prl, ra
    ldi @delay.high
    mov prh, ra
    jmp

after_off_delay:
    ldi @main_loop.low
    mov prl, ra
    ldi @main_loop.high
    mov prh, ra
    jmp


; delay(RB)
; RB = approximate milliseconds when CLOCK_HZ = 1_000_000
; LINK_RET_L/H = return address
delay:
delay_outer:
    mov rd, rb
    ldi #0
    cmp ra
    ldi @delay_return.low
    mov prl, ra
    ldi @delay_return.high
    mov prh, ra
    jeq

    ; middle loop counter lives in RAM so RD can be reused by inner loop
    ldi #0
    mov marh, ra
    ldi $DELAY_SLOT
    mov marl, ra
    ldi $DELAY_MID_COUNT
    mov m, ra

delay_middle:
    ldi $DELAY_INNER_COUNT
    mov rd, ra

delay_inner:
    nop
    nop
    nop
    nop

    ldi #1
    sub ra
    mov rd, acc

    ldi #0
    cmp ra
    ldi @delay_inner.low
    mov prl, ra
    ldi @delay_inner.high
    mov prh, ra
    jne

    ; decrement middle counter in RAM
    ldi #0
    mov marh, ra
    ldi $DELAY_SLOT
    mov marl, ra
    mov rd, m
    ldi #1
    sub ra
    mov m, acc
    mov rd, acc

    ldi #0
    cmp ra
    ldi @delay_middle.low
    mov prl, ra
    ldi @delay_middle.high
    mov prh, ra
    jne

    ; decrement outer counter in RB
    mov rd, rb
    ldi #1
    sub ra
    mov rb, acc

    ldi @delay_outer.low
    mov prl, ra
    ldi @delay_outer.high
    mov prh, ra
    jmp

delay_return:
    ldi #0
    mov marh, ra

    ldi $LINK_RET_L
    mov marl, ra
    mov ra, m
    mov prl, ra

    ldi $LINK_RET_H
    mov marl, ra
    mov ra, m
    mov prh, ra

    jmp
