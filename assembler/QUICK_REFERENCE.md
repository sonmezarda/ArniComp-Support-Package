# ArniComp Assembler Quick Reference

## Syntax Rules

- Comments start with `;`
- Constants use `equ NAME expr`
- Labels may stand alone or share a line with an instruction: `loop:` / `done: HLT`
- Local labels use `*name:` and are referenced as `@*name`
- Prefixes:
  - `#` direct number or character literal: `#10`, `#0x2A`, `#0b1010`, `#'A'`
  - `$` constant reference: `$COUNT`
  - `@` label reference: `@loop`
- Bit slices use `value[hi:lo]`:
  - `@target[7:0]`
  - `@target[15:8]`
  - `$CONST[4:0]`
  - `$CONST[7:5]`
- Helper functions:
  - `LOW(x)` / `BYTE0(x)`
  - `HIGH(x)` / `BYTE1(x)`
  - `BITS(x, hi, lo)`

Local-label example:

```assembly
my_func:
*loop:
    JEQ @*done
    JMP @*loop
*done:
    RET
```

## Preprocessor and Layout

```assembly
.include "common.asm"
.import "../lib/math.asm" mul_u8

.repeat 4 {
    NOP
}

.define FPGA 1
.if FPGA
    NOP
.else
    HLT
.endif

.fill 16
.org 0x100, #0xFF
.align 16
```

## Registers

### Destinations

| Register | Notes |
|----------|-------|
| RA | General-purpose |
| RD | General-purpose |
| RB | General-purpose |
| MARL | Memory address low |
| MARH | Memory address high |
| PRL | Program register low |
| PRH | Program register high |
| M | Memory at `[MARH:MARL]` |

### Sources

| Register | Notes |
|----------|-------|
| RA | General-purpose |
| RD | General-purpose |
| RB | General-purpose |
| ACC | ALU result / accumulator |
| ZERO | Zero source |
| LRL | Link register low |
| LRH | Link register high |
| M | Memory at `[MARH:MARL]` |

Notes:

- `0` and `#0` are accepted where a zero source alias is allowed.
- `LDL` and `LDH` may target only `RA` or `RD`.

### PUSH Source Set

`PUSH` does not use the normal global source map. Valid `PUSH` sources are:

- `RA`
- `RD`
- `RB`
- `ACC`
- `MARH`
- `LRL`
- `LRH`
- `MARL`

## Real ISA Instructions

### Loads

```assembly
LDL RA, #5
LDL RD, $CONST[4:0]
LDH RA, #7
LDH RD, @target[7:5]
```

### Data Movement

```assembly
MOV RA, RD
MOV MARL, RA
MOV PRH, ZERO
MOV M, RA
```

### Arithmetic and Logic

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

### Stack and Flow

```assembly
PUSH RA
PUSH MARL
PUSH MARH
PUSH LRL
PUSH LRH
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
```

### Accepted Jump Aliases

These are assembler aliases for real jump conditions:

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

## Pseudoinstructions and Macros

These expand into one or more real ISA instructions.

```assembly
LDI #10
LDI 'A'
LDI #'A'
LDI RD, $CONST
LDI RA, @label[7:0]

CLR RA

CALL target
CALL target :RD
JMPA target
JMPA target :RD

RET
RET :STACK

PUSHI #5
PUSHI 'A' :RD
PUSHSTR "OK"
PUSHSTR "HELLO", '\0' :RD

JLE
JGE
JLEU
```

Target-taking jump forms are also supported:

```assembly
JMP target
JEQ done
JNE loop :RD
JLE finish
JGE retry :RD
JLEU done
JGTU retry :RD
```

Notes:

- Target-taking jumps load `PRL/PRH` with the target address, then emit the requested jump.
- Default temporary register is `RA`; `:RD` is also supported.
- `JGEU` and `JLTU` are aliases for `JCS` and `JCC`.
- `JLEU` is a macro over `JCC` and `JEQ`.
- `JGTU` is only valid with an explicit target operand.

## Bit Slices and Address Loading

```assembly
equ CONST 0x1234

LDL RA, $CONST[4:0]
LDH RD, $CONST[7:5]

LDL RA, @target[4:0]
LDH RD, @target[7:5]

LDI RA, #0x1234[15:8]
LDI LOW(@target)
LDI HIGH(@target)
```

Rules:

- `LDL` accepts only 5-bit values or 5-bit slices.
- `LDH` accepts only 3-bit values or 3-bit slices.
- `LDI` and `PUSHI` accept an unsliced byte value or an explicit 8-bit slice.
- Unsliced `LDI` operands above `0xFF` are truncated to the low byte with a warning.

## Common Patterns

### Absolute Jump

```assembly
JMPA target

; Manual equivalent
LDI RA, @target[7:0]
MOV PRL, RA
LDI RA, @target[15:8]
MOV PRH, RA
JMP
```

### Call and Return

```assembly
CALL worker
RET
RET :STACK
```

## Common Pitfalls

```assembly
@label.low          ; WRONG: old syntax
@label.high         ; WRONG: old syntax
ADD #1              ; WRONG: use ADDI
SUB #1              ; WRONG: use SUBI
PUSH ZERO           ; WRONG: not supported anymore
PUSH M              ; WRONG: not supported anymore
SMSBRA              ; WRONG: legacy mnemonic
INX                 ; WRONG: legacy mnemonic
```

Use these instead:

```assembly
@label[7:0]
@label[15:8]
ADDI #1
SUBI #1
PUSH MARH
PUSH MARL
```

## CLI Commands

```bash
python main.py assemble program.asm output.txt
python main.py assemble program.asm output.txt --listing program.lst --listing-mode both
python main.py createsvhex program.asm program.mem --listing program.lst --listing-mode asm
python main.py createsvmi program.asm program.mi --depth 2048 --listing program.lst --listing-mode asm
python main.py creategowinprom program.asm ../verilog/src/gowin_prom/gowin_prom.v --depth 2048
python main.py disassemble program.txt output.asm
python main.py createbin program.txt program.bin
python main.py load program.bin
python main.py loadasm program.asm
python main.py help
```

Listing modes: `hex`, `asm`, `both`
