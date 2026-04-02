# ArniComp Assembler

Final ISA assembler for ArniComp's 8-bit CPU.

## Overview

- Line-based parser, no separate lexer/AST layer
- `equ` constants with simple integer expressions
- `label:` definitions with iterative address resolution
- Final ISA encoder plus a small disassembler
- Pseudoinstructions:
  - `LDI [RA|RD,] value`
  - `CLR dst`

## Constants

`equ` supports integer expressions and single-character literals.

```assembly
equ ON_CHAR 'A'
equ OFF_CHAR 'B'
equ NEXT_CHAR 'A' + 1
```

## Registers

### Destinations

- `RA`
- `RD`
- `RB`
- `MARL`
- `MARH`
- `PRL`
- `PRH`
- `M`

### Sources

- `RA`
- `RD`
- `RB`
- `ACC`
- `ZERO`
- `LRL`
- `LRH`
- `M`

`0` and `#0` are also accepted where a zero-source alias is allowed.

## Instructions

### Loads

```assembly
LDL RA, #5
LDL RD, #31
LDH RA, #7
LDH RD, #3

LDI #10
LDI 'A'
LDI #'A'
LDI RD, #125
LDI RA, $CONST
LDI RD, @label
```

### Data movement

```assembly
MOV RA, RD
MOV MARL, RA
MOV RA, 0
MOV RA, #0
MOV RA, ZERO
CLR RA
```

### Arithmetic / logic

```assembly
ADD RA
ADDI #3
ADC M
SUB RB
SUBI #2
SBC LRL
CMP M
NOT RA
XOR RD
AND RB
```

### Stack / flow

```assembly
PUSH RA
POP RD

NOP
HLT
INC #1
INC #2
DEC #1
DEC #2
JAL

JMP
JEQ
JNE
JCS
JCC
JMI
JVS
JLT
JGT
JLE
JGE
```

### Jump aliases

```assembly
JZ
JNZ
JC
JNC
JN
JV
JGEU
JLTU
JLTS
```

### Jump encoding

Canonical jump condition bits now use this order:

```text
JEQ = 000
JNE = 001
JCS = 010
JCC = 011
JMI = 100
JVS = 101
JLT = 110
JMP = 111
```

This keeps unconditional jump on `111`, matching `JAL = 00000111` on its low 3 bits.

## Bit Slices

The assembler supports general `value[hi:lo]` slices on numeric literals, constants, and labels.

```assembly
equ CONST 0x1234

LDL RA, $CONST[4:0]
LDH RD, $CONST[7:5]

LDL RA, @target[4:0]
LDH RD, @target[7:5]

LDI RA, #0x1234[15:8]
```

Notes:

- `LDL` accepts only 5-bit values or 5-bit slices.
- `LDH` accepts only 3-bit values or 3-bit slices.
- `LDI` accepts an unsliced value or an explicit 8-bit slice.

## Labels and Address Loading

Jumps do not take label operands. They jump to the address already present in `PRH:PRL`.

```assembly
target:
    NOP

    LDI RA, @target
    MOV PRL, RA
    LDI RA, #0
    MOV PRH, RA
    JMP
```

If an unsliced `LDI` operand resolves above `0xFF`, the assembler loads only the low byte and emits a warning.

## Commands

```bash
python main.py assemble program.asm output.txt
python main.py disassemble program.txt output.asm
python main.py createbin program.txt program.bin
python main.py load program.bin
python main.py help
```

## Verification

Run the included verification script:

```bash
python verify_final_isa.py
```

## Migration Notes

- Old `LDI` is now a pseudoinstruction over `LDL` and `LDH`.
- `LDI` still defaults to `RA`, but now `LDI RD, ...` is also valid.
- Old label suffix syntax like `@label.low` / `@label.high` was replaced by bit slices such as `@label[7:0]`, `@label[15:8]`, `@label[4:0]`, `@label[7:5]`.
- Immediate arithmetic must be written explicitly as `ADDI` or `SUBI`.
- `ADD #imm` and `SUB #imm` are rejected with guidance.
- `JGT` now uses the formerly reserved opcode `00000110`.
- `JMP` now uses jump-condition bits `111`.
- `JLE` is supported as an assembler macro and expands to `JEQ` followed by `JLT`.
- `JGE` is supported as an assembler macro and expands to `JEQ` followed by `JGT`.
- Legacy mnemonics outside the final ISA, such as `SMSBRA`, `INX`, and the old `JGT/JGE/JLE` semantics, are no longer accepted.
