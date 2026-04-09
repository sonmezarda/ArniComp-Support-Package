equ SYS_LED_H 0x0C
equ SYS_LED_L 0x00
equ UART_BASE_H 0x09
equ UART_CNTRL_L 0x40 ; {5'b0, TX_EN, RX_EN, UART_EN}
equ UART_BAUDSEL_L 0x20
equ UART_TX_DATA_L 0x10

equ O_C 'O'
equ X_C 'X'
equ J_C 'J'
equ A_C 'A'

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

    ldi $UART_TX_DATA_L
    mov marl, ra

    ldi $UART_BASE_H
    mov marh, ra

; Test 1: JEQ taken should skip the next instruction
test_jeq:
    ldi $X_C
    mov rb, ra
    ldi #0
    mov rd, ra
    cmp ra

    ldi @jeq_taken
    mov prl, ra
    jeq

    mov m, rb ; must not execute if there is no delay slot

jeq_taken:
    ldi $O_C
    mov m, ra

; Test 2: JMP should skip the next instruction
test_jmp:
    ldi $X_C
    mov rb, ra
    ldi @jmp_taken
    mov prl, ra
    jmp

    mov m, rb ; must not execute if there is no delay slot

jmp_taken:
    ldi $J_C
    mov m, ra

; Test 3: JAL should jump immediately and return correctly
test_jal:
    ldi $X_C
    mov rb, ra
    ldi @after_jal
    mov prl, ra
    jal

    mov m, rb ; must not execute if there is no delay slot

after_jal:
    ldi $A_C
    mov m, ra

    ldi $SYS_LED_H
    mov marh, ra
    ldi $SYS_LED_L
    mov marl, ra
    ldi #0x2D
    mov m, ra
    hlt
    hlt
