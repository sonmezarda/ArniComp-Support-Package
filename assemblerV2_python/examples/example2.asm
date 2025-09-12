; Register hareketleri ve AND
LDI #10
MOV PRL, RA
MOV RA, CLR
ADDI #7
MOV RD, RA
AND RD
SBC RD ; test amaçlı (flags yoksa yine binary çıkar)
JEQ
JNE
HLT
