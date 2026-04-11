; ArniComp function ABI / scratch-page include
; Recommended shared scratch page: 0x0000..0x001F
; This page is a simple global convention, not an automatic stack frame.
; Recursive and nested-call-heavy code must use it carefully.

equ F_TMP_BASE_H   0x00

; Single-byte scratch slots
equ F_T0_L       0x00
equ F_T1_L       0x01
equ F_T2_L       0x02
equ F_T3_L       0x03
equ F_T4_L       0x04
equ F_T5_L       0x05
equ F_T6_L       0x06
equ F_T7_L       0x07

; Suggested 16-bit scratch words
equ F_W0_LO_L   0x10
equ F_W0_HI_L   0x11
equ F_W1_LO_L   0x12
equ F_W1_HI_L   0x13

; Suggested extra-argument spill slots
equ F_A2_L       0x18
equ F_A3_L       0x19
equ F_A4_L       0x1A
equ F_A5_L       0x1B
