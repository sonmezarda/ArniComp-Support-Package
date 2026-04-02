# ArniComp Assembler

Final ISA assembler for ArniComp's 8-bit CPU.

## Overview

- Line-based parser, no separate lexer/AST layer
- `equ` constants with simple integer expressions
- `label:` definitions with iterative address resolution
- labels can share a line with an instruction, for example `done: HLT`
- `.include "path"` support with relative-path resolution
- `.repeat N { ... }` preprocessing blocks
- helper functions: `LOW(...)`, `HIGH(...)`, `BYTE0(...)`, `BYTE1(...)`, `BITS(...)`
- layout directives: `.org`, `.align`, `.fill`
- conditional assembly: `.define`, `.if`, `.else`, `.endif`
- optional listing/debug output for assembled source
- `PUSHSTR "text"[, trailingValue] [:RA|:RD]`
- Final ISA encoder plus a small disassembler
- Pseudoinstructions:
  - `LDI [RA|RD,] value`
  - `CLR dst`
  - `CALL target [:RA|:RD]`
  - `JMPA target [:RA|:RD]`
  - `RET`
  - `RET :STACK`
  - `PUSHI value [:RA|:RD]`

## Constants

`equ` supports integer expressions and single-character literals.

```assembly
equ ON_CHAR 'A'
equ OFF_CHAR 'B'
equ NEXT_CHAR 'A' + 1
```

## Labels

Both forms are accepted:

```assembly
loop:
    nop

done: hlt
```

## Includes

The assembler supports quoted include paths resolved relative to the current file.

```assembly
.include "common/uart.inc"
.include "../shared/constants.inc"
```

Notes:

- Includes are expanded before constant extraction and label resolution.
- Relative paths are resolved from the file that contains the `.include`.
- Recursive include chains are rejected with a clear error.

## Repeat Blocks

The assembler supports simple preprocessing repeats:

```assembly
.repeat 4 {
    nop
}
```

This expands before constant extraction and label resolution.

Notes:

- Nested `.repeat` blocks are supported.
- The repeat count is an integer expression.
- The current syntax requires `{` on the `.repeat` line and a standalone closing `}` line.

## Conditional Assembly

The preprocessor supports simple build-time symbols and conditional blocks:

```assembly
.define FPGA 1

.if FPGA
    NOP
.else
    HLT
.endif
```

Notes:

- `.define NAME expr` creates a preprocessor symbol.
- `.if expr` evaluates the expression using currently defined symbols.
- Nested `.if/.else/.endif` blocks are supported.
- Undefined symbols in `.if` expressions are treated as errors.

## Layout Directives

The assembler supports a small set of ROM layout directives:

```assembly
.fill 16
.fill 8, #0xFF

.org 0x100
.org 0x200, #0xFF

.align 16
.align 32, #0xFF
```

Behavior:

- `.fill count[, byte]`
  - emits `count` copies of `byte`
  - default fill byte is `0x00`
- `.org address[, byte]`
  - pads from the current address up to `address`
  - default fill byte is `0x00`
  - moving backward is an error
- `.align boundary[, byte]`
  - pads until the current address is aligned to `boundary`
  - default fill byte is `0x00`

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

## Real ISA Instructions

These mnemonics map directly to real 8-bit opcodes.

### Loads

```assembly
LDL RA, #5
LDL RD, #31
LDH RA, #7
LDH RD, #3

```

### Data movement

```assembly
MOV RA, RD
MOV MARL, RA
MOV RA, 0
MOV RA, #0
MOV RA, ZERO
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
```

### Jump aliases

These are accepted assembler aliases for real jump conditions:

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

## Assembler Pseudoinstructions / Macros

These do not correspond to a single real opcode. The assembler expands them into one or more real instructions.

```assembly
LDI #10
LDI 'A'
LDI #'A'
LDI RD, #125
LDI RA, $CONST
LDI RD, @label

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

JLE
JGE
```

Conditional and unconditional jumps may also take an absolute target label or constant address as assembler pseudoinstructions:

```assembly
JEQ done
JNE loop :RD
JMP target
JLE finish
JGE retry :RD
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

When a jump takes a target operand, the assembler treats it as a pseudoinstruction:

- it loads `PRL/PRH` with the target address
- then emits the requested jump instruction

Default temporary register is `RA`; `:RD` is also supported.

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

## Helper Functions

The assembler also supports helper functions inside expressions and operands:

```assembly
equ LO LOW(0x1234)
equ HI HIGH(0x1234)
equ MID BITS(0xE5, 7, 5)

LDI LOW(@target)
LDI HIGH(@target)
LDL RA, BITS($CONST, 4, 0)
LDH RD, BITS($CONST, 7, 5)
```

Supported helpers:

- `LOW(x)` / `BYTE0(x)` -> `x & 0xFF`
- `HIGH(x)` / `BYTE1(x)` -> `(x >> 8) & 0xFF`
- `BITS(x, hi, lo)` -> inclusive bit extraction

## Labels and Address Loading

Bare jump instructions do not take label operands. They jump to the address already present in `PRH:PRL`.

```assembly
target:
    NOP

    LDI RA, @target
    MOV PRL, RA
    LDI RA, #0
    MOV PRH, RA
    JMP
```

The assembler also supports target-taking jump pseudoinstructions:

```assembly
JMP target
JEQ done
JNE loop :RD
JLE finish
JGE retry :RD
```

These expand to:

- load `PRL/PRH` with the target address
- then emit the requested jump instruction

If an unsliced `LDI` operand resolves above `0xFF`, the assembler loads only the low byte and emits a warning.

## CALL Pseudoinstruction

`CALL` loads `PRL/PRH` with an absolute target address and then emits `JAL`.

Supported forms:

```assembly
CALL target
CALL @target
CALL target :RD
CALL $CONST_ADDR :RA
```

Notes:

- Default temporary register is `RA`.
- `:RD` selects `RD` as the temporary register.
- Bare label names are accepted for convenience.
- If the high byte of the target address is zero, the assembler emits `MOV PRH, ZERO` instead of loading it through the temporary register.

## JMPA Pseudoinstruction

`JMPA` loads `PRL/PRH` with an absolute target address and then emits `JMP`.

Supported forms:

```assembly
JMPA target
JMPA @target
JMPA target :RD
JMPA $CONST_ADDR :RA
```

Notes:

- Default temporary register is `RA`.
- `:RD` selects `RD` as the temporary register.
- Bare label names are accepted for convenience.
- If the high byte of the target address is zero, the assembler emits `MOV PRH, ZERO`.

## RET Pseudoinstruction

Supported forms:

```assembly
RET
RET :STACK
```

Behavior:

- `RET`

```assembly
MOV PRL, LRL
MOV PRH, LRH
JMP
```

- `RET :STACK`

```assembly
POP PRH
POP PRL
JMP
```

Stack note:

- `RET :STACK` expects the return address to be stacked with low byte pushed first and high byte pushed second.
- That means the high byte is on top of the stack when returning.

## PUSHI Pseudoinstruction

`PUSHI` loads an 8-bit value into a temporary register and then pushes that register.

Supported forms:

```assembly
PUSHI #5
PUSHI 'A'
PUSHI $CONST[7:0]
PUSHI #5 :RD
```

Notes:

- Default temporary register is `RA`.
- `:RD` selects `RD` as the temporary register.
- `PUSHI` uses the same byte-loading rules as `LDI`.
- Explicit slices must be exactly 8 bits wide.

## PUSHSTR Pseudoinstruction

`PUSHSTR` pushes a string in a pop-friendly order, so repeated `POP` operations produce the string in normal reading order.

Supported forms:

```assembly
PUSHSTR "OK"
PUSHSTR "HELLO", '\0'
PUSHSTR "A" :RD
```

Behavior:

- Characters are pushed in reverse order internally so that later `POP`s yield the original string order.
- Optional trailing values are pushed before the string body, also in pop-friendly order.
- Default temporary register is `RA`.
- `:RD` selects `RD` as the temporary register.

## Commands

```bash
python main.py assemble program.asm output.txt
python main.py assemble program.asm output.txt --listing program.lst --listing-mode both
python main.py createsvhex program.asm program.mem --listing program.lst --listing-mode asm
python main.py disassemble program.txt output.asm
python main.py createbin program.txt program.bin
python main.py load program.bin
python main.py help
```

## Listing Output

`assemble` and `createsvhex` can optionally emit a listing/debug file:

```bash
python main.py assemble program.asm output.txt --listing program.lst --listing-mode both
python main.py createsvhex program.asm program.mem --listing program.lst --listing-mode asm
```

Supported modes:

- `hex`
  - grouped by source file
  - shows address + emitted hex bytes
  - shows the original source line on the next line
- `asm`
  - grouped by source file
  - shows the original source line
  - shows each emitted machine byte disassembled as a real instruction
- `both`
  - includes both views together

Each listing includes:

- final ROM address
- emitted bytes in hex
- source file and line number
- original source text

Example:

```text
; Source: program.asm
0000  00
      [1] start: NOP
0001  C4 A8 B4 07
      [2] CALL done
0005  01
      [3] done: HLT
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
