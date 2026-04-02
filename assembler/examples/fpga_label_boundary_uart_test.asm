equ SYS_LED_H 0x0C
equ SYS_LED_L 0x00
equ UART_BASE_H 0x09
equ UART_CNTRL_L 0x40 ; {5'b0, TX_EN, RX_EN, UART_EN}
equ UART_BAUDSEL_L 0x20
equ UART_TX_DATA_L 0x10

equ O_C 'O'
equ K_C 'K'
equ F_C 'F'
equ ONE_C '1'
equ TWO_C '2'
equ THREE_C '3'
equ FOUR_C '4'
equ FIVE_C '5'
equ SIX_C '6'
equ NEWLINE_C '\n'

equ PASS_LEN 3
equ FAIL_LEN 3

setup:
    ldi #0
    mov prh, ra
    mov prl, ra
    mov marl, ra
    mov marh, ra

    ldi $UART_BASE_H
    mov marh, ra

    ldi $UART_CNTRL_L
    mov marl, ra

    ldi #0b00000101
    mov m, ra ; enable tx and uart

    ldi $UART_BAUDSEL_L
    mov marl, ra

    ldi #2
    mov m, ra ; baud = 9600

; Case 1: reconstruct low byte 0xFF with LDL/LDH slices
case1:
    ldl ra, @label_ff[4:0]
    ldh ra, @label_ff[7:5]
    mov rd, ra
    ldi #0xFF
    cmp ra

    ldi @case2
    mov prl, ra
    jeq

    ldi $ONE_C
    mov rb, ra
    ldi @fail
    mov prl, ra
    jmp

; Case 2: reconstruct low byte 0x00 for 0x0100 with LDL/LDH slices
case2:
    ldl ra, @label_100[4:0]
    ldh ra, @label_100[7:5]
    mov rd, ra
    ldi #0
    cmp ra

    ldi @case3
    mov prl, ra
    jeq

    ldi $TWO_C
    mov rb, ra
    ldi @fail
    mov prl, ra
    jmp

; Case 3: LDI @label_100[15:8] should be 0x01
case3:
    ldi @label_100[15:8]
    mov rd, ra
    ldi #1
    cmp ra

    ldi @case4
    mov prl, ra
    jeq

    ldi $THREE_C
    mov rb, ra
    ldi @fail
    mov prl, ra
    jmp

; Case 4: direct low 5 bits of 0x00FF should be 31
case4:
    ldl ra, @label_ff[4:0]
    mov rd, ra
    ldi #31
    cmp ra

    ldi @case5
    mov prl, ra
    jeq

    ldi $FOUR_C
    mov rb, ra
    ldi @fail
    mov prl, ra
    jmp

; Case 5: direct bits [7:5] of 0x00FF should be loaded into the high bits.
; With RA cleared first, LDH RA, @label_ff[7:5] should produce 0xE0.
case5:
    ldi #0
    ldh ra, @label_ff[7:5]
    mov rd, ra
    ldi #0xE0
    cmp ra

    ldi @case6
    mov prl, ra
    jeq

    ldi $FIVE_C
    mov rb, ra
    ldi @fail
    mov prl, ra
    jmp

; Case 6: LDI @label_ff[15:8] should be 0x00
case6:
    ldi @label_ff[15:8]
    mov rd, ra
    ldi #0
    cmp ra

    ldi @pass
    mov prl, ra
    jeq

    ldi $SIX_C
    mov rb, ra
    ldi @fail
    mov prl, ra
    jmp

pass:
    ldi $NEWLINE_C
    push ra
    ldi $K_C
    push ra
    ldi $O_C
    push ra
    ldi $PASS_LEN
    mov rd, ra

    ldi @send_len_func
    mov prl, ra
    jal

    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    ldi #0x1B
    mov m, ra
    hlt
    hlt

fail:
    ldi $NEWLINE_C
    push ra
    push rb
    ldi $F_C
    push ra
    ldi $FAIL_LEN
    mov rd, ra

    ldi @send_len_func
    mov prl, ra
    jal

    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    ldi #0x0B
    mov m, ra
    hlt
    hlt

send_len_func:
    ldi $UART_TX_DATA_L
    mov marl, ra

    ldi $UART_BASE_H
    mov marh, ra

send_loop:
    pop rb
    mov m, rb

    subi #1
    mov rd, acc

    ldi @end_loop
    mov prl, ra
    jeq

    ldi @send_loop
    mov prl, ra
    jmp

end_loop:
    mov prl, lrl
    mov prh, lrh
    jmp

; Padding region to force boundary labels near 0x00FF / 0x0100.
pad_000:
    nop
pad_001:
    nop
pad_002:
    nop
pad_003:
    nop
pad_004:
    nop
pad_005:
    nop
pad_006:
    nop
pad_007:
    nop
pad_008:
    nop
pad_009:
    nop
pad_010:
    nop
pad_011:
    nop
pad_012:
    nop
pad_013:
    nop
pad_014:
    nop
pad_015:
    nop
pad_016:
    nop
pad_017:
    nop
pad_018:
    nop
pad_019:
    nop
pad_020:
    nop
pad_021:
    nop
pad_022:
    nop
pad_023:
    nop
pad_024:
    nop
pad_025:
    nop
pad_026:
    nop
pad_027:
    nop
pad_028:
    nop
pad_029:
    nop
pad_030:
    nop
pad_031:
    nop
pad_032:
    nop
pad_033:
    nop
pad_034:
    nop
pad_035:
    nop
pad_036:
    nop
pad_037:
    nop
pad_038:
    nop
pad_039:
    nop
pad_040:
    nop
pad_041:
    nop
pad_042:
    nop
pad_043:
    nop
pad_044:
    nop
pad_045:
    nop
pad_046:
    nop
pad_047:
    nop
pad_048:
    nop
pad_049:
    nop
pad_050:
    nop
pad_051:
    nop
pad_052:
    nop
pad_053:
    nop
pad_054:
    nop
pad_055:
    nop
pad_056:
    nop
pad_057:
    nop
pad_058:
    nop
pad_059:
    nop
pad_060:
    nop
pad_061:
    nop
pad_062:
    nop
pad_063:
    nop
pad_064:
    nop
pad_065:
    nop
pad_066:
    nop
pad_067:
    nop
pad_068:
    nop
pad_069:
    nop
pad_070:
    nop
pad_071:
    nop
pad_072:
    nop
pad_073:
    nop
pad_074:
    nop
pad_075:
    nop
pad_076:
    nop
pad_077:
    nop
pad_078:
    nop
pad_079:
    nop
pad_080:
    nop
pad_081:
    nop
label_ff:
    nop
label_100:
    nop
