.include "../includes/uart.inc"

.define USE_RD 1

entry:
    .if USE_RD
    call setup_uart :RD
    .else
    call setup_uart
    .endif

    jmpa done :RD

setup_uart:
    pushi 'A' :RD
    pushstr "OK", '\0' :RD
    ret

done: hlt
      hlt
