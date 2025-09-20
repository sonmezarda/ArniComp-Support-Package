

ldi #0b1111111
mov rd, ra ; rd = 0x7F
add ra ; acc = 0xFE
add acc ; acc = 0x7F + 0xFE = 0x17D -> 0x7D with carry

mov ml, acc ; ml = 0x7D

adc acc ; acc = rd + acc + carry
; acc = 0x7F + 0x7D + 1  =  FD

ldi #1
mov marl, ra

mov ml, acc
HLT

