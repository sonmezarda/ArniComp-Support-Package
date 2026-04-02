start: nop

.repeat 2 {
    nop
}

.fill 2, #0xAA
.align 8, #0x7E
.org 12, #0xFF

done: hlt
