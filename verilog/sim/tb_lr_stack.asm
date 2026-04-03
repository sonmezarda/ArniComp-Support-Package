; LRL/LRH stack regression for nested calls

start:
    call func1
    hlt
    hlt

func1:
    push lrl
    push lrh
    call func2
    ret :stack

func2:
    ldi #0x5A
    mov rb, ra
    ret
