; Basit örnek
LDI #5
MOV RD, RA ; RA -> RD
ADDI #3
SUBI #2
ADD RD
MOV RA, RA ; (örnek amaçlı ACC yerine RA, çünkü ACC destination kodlamasında yok)
JMP
HLT
