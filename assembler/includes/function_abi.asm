; ArniComp function ABI / virtual-register-page include
; Recommended shared page: 0x0000..0x001F
; This page is a global convention, not an automatic stack frame.
; The page is split into virtual-register banks:
;   VT = caller-clobbered temp
;   VS = preserved by convention
;   VA = optional argument/spill window

equ F_VR_BASE_H   0x00
equ F_TMP_BASE_H  0x00

; VT: caller-clobbered temp virtual registers
equ F_VT0_L      0x00
equ F_VT1_L      0x01
equ F_VT2_L      0x02
equ F_VT3_L      0x03
equ F_VT4_L      0x04
equ F_VT5_L      0x05
equ F_VT6_L      0x06
equ F_VT7_L      0x07
equ F_VT8_L      0x08
equ F_VT9_L      0x09
equ F_VT10_L     0x0A
equ F_VT11_L     0x0B
equ F_VT12_L     0x0C
equ F_VT13_L     0x0D
equ F_VT14_L     0x0E
equ F_VT15_L     0x0F

; VS: preserved virtual registers
equ F_VS0_L      0x10
equ F_VS1_L      0x11
equ F_VS2_L      0x12
equ F_VS3_L      0x13
equ F_VS4_L      0x14
equ F_VS5_L      0x15
equ F_VS6_L      0x16
equ F_VS7_L      0x17

; VA: optional argument / spill virtual registers
equ F_VA0_L      0x18
equ F_VA1_L      0x19
equ F_VA2_L      0x1A
equ F_VA3_L      0x1B
equ F_VA4_L      0x1C
equ F_VA5_L      0x1D
equ F_VA6_L      0x1E
equ F_VA7_L      0x1F

; Backward-compatible aliases
equ F_T0_L       F_VT0_L
equ F_T1_L       F_VT1_L
equ F_T2_L       F_VT2_L
equ F_T3_L       F_VT3_L
equ F_T4_L       F_VT4_L
equ F_T5_L       F_VT5_L
equ F_T6_L       F_VT6_L
equ F_T7_L       F_VT7_L

equ F_W0_LO_L    F_VT8_L
equ F_W0_HI_L    F_VT9_L
equ F_W1_LO_L    F_VT10_L
equ F_W1_HI_L    F_VT11_L

equ F_A2_L       F_VA0_L
equ F_A3_L       F_VA1_L
equ F_A4_L       F_VA2_L
equ F_A5_L       F_VA3_L
