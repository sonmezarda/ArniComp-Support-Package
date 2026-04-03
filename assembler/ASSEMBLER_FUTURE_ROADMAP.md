# Assembler Future Roadmap

This document captures proposed quality-of-life and power-user features for the ArniComp assembler after the final ISA migration.

## Goals

- Reduce repetitive handwritten boilerplate for calls, jumps, stack usage, and string output.
- Keep low-level control available for optimized hand-written assembly.
- Add common assembler conveniences without hiding machine behavior.
- Preserve explicitness where instruction count or register choice matters.

## Status

- [x] `.include`
- [x] `CALL`
- [x] `JMPA`
- [x] `RET`
- [x] `PUSHI`
- [ ] `DB/DW/ASCII/ASCIIZ`
- [x] `.repeat`
- [x] `LOW/HIGH/BITS`
- [x] `.org/.align/.fill`
- [x] conditional assembly
- [x] listing/debug output
- [x] selected function-library imports

## Internal Refactor Direction

- `AssemblyHelper` should remain the orchestration layer for parsing, symbol resolution, and final encoding.
- Preprocess concerns such as includes and future conditional assembly should move toward dedicated helper modules.
- Macro and pseudoinstruction expansion should live outside `AssemblyHelper`.
- Current status:
  - include expansion is already isolated conceptually as a preprocessing stage
  - macro handling has started moving into a dedicated `MacroExpander` module
- preprocess handling has moved into a dedicated `Preprocessor` module

## Guiding Principles

1. Default behavior should be convenient but predictable.
2. Advanced syntax should still expose exact codegen when it matters.
3. Features that can silently change code size should be documented clearly.
4. Hand-written low-level assembly must remain a first-class workflow.

## Planned Features

### 1. Call / Jump Macros

#### `call label`

Add a pseudoinstruction that expands into:

```asm
LDI @label[7:0]
MOV PRL, <tmp>
LDI @label[15:8]
MOV PRH, <tmp>
JAL
```

Default temporary register:

- `RA`

Optional explicit temporary register syntax:

```asm
CALL target :RD
CALL target :RA
```

Notes:

- The assembler should optimize low-byte-only cases when the high byte is known to be zero (MOV PRH, ZERO).
- The expansion must be deterministic and documented.
- The chosen temporary register should control whether the generated `LDI/LDL/LDH` sequence targets `RA` or `RD`.

Status:

- Implemented
- Supported forms:
  - `CALL target`
  - `CALL @target`
  - `CALL target :RA`
  - `CALL target :RD`
- Default temporary register is `RA`
- Bare label names are accepted
- If the target high byte is zero, the assembler emits `MOV PRH, ZERO`

#### `jmpa label`

Add an absolute jump pseudoinstruction similar to `call`, but ending with `JMP` instead of `JAL`.

Suggested syntax:

```asm
JMPA target
JMPA target :RD
```

Expansion idea:

```asm
LDI @label[7:0]
MOV PRL, <tmp>
LDI @label[15:8]
MOV PRH, <tmp>
JMP
```

Status:

- Implemented
- Supported forms:
  - `JMPA target`
  - `JMPA @target`
  - `JMPA target :RA`
  - `JMPA target :RD`
- Default temporary register is `RA`
- Bare label names are accepted
- If the target high byte is zero, the assembler emits `MOV PRH, ZERO`
- Conditional jumps now also support target operands with the same `:RA` / `:RD` temporary-register selection model

#### `ret`

Support two return forms:

```asm
RET
RET :STACK
```

Planned meaning:

- `RET`:

```asm
MOV PRL, LRL
MOV PRH, LRH
JMP
```

- `RET :STACK`:
  pop the return address from the stack and jump through `PRL/PRH`

One possible expansion:

```asm
POP PRH      ; high byte on top of stack
POP PRL      ; low byte below it
JMP
```

Status:

- Implemented
- Supported forms:
  - `RET`
  - `RET :STACK`
- `RET` returns via `LRL/LRH`
- `RET :STACK` expects low byte pushed first, high byte pushed second

### 2. Stack Convenience Macros

#### `pushi value`

Push an immediate value without manually loading a register first.

Suggested syntax:

```asm
PUSHI #65
PUSHI 'A'
PUSHI @label[7:0]
PUSHI #65 :RD
```

Default temporary register:

- `RA`

Expansion:

```asm
LDI <tmp>, value
PUSH <tmp>
```

Status:

- Implemented
- Supported forms:
  - `PUSHI #65`
  - `PUSHI 'A'`
  - `PUSHI $CONST[7:0]`
  - `PUSHI #65 :RD`
- Default temporary register is `RA`
- `:RD` selects `RD` as the temporary register
- Uses the same byte-loading rules as `LDI`

#### `pushstr`

Push a short literal string onto the stack in expansion order suitable for later popping.

Suggested syntax:

```asm
PUSHSTR "HELLO"
PUSHSTR "HELLO", 0
PUSHSTR "HELLO\n", '\0'
PUSHSTR "HELLO" :RD
```

Planned behavior:

- Expand to repeated `PUSHI` operations.
- Optionally append a terminator or explicit trailing values.
- Preserve escape handling such as `\n`, `\r`, `\t`, `\0`.
- Add Reverse option.

Reverse:
```asm
PUSHSTR "HELLO" :RD :reverse
PUSHSTR "Hello", 0 :reverse
.
.
.
```

Status:

- Implemented in its basic form
- Supported forms:
  - `PUSHSTR "HELLO"`
  - `PUSHSTR "HELLO", '\0'`
  - `PUSHSTR "HELLO" :RA`
  - `PUSHSTR "HELLO" :RD`
- Default behavior is pop-friendly string order
- Future extension still possible for an explicit reverse/alternate mode
### 3. Data Definition Directives

Add standard data emitters.

#### `DB`

Define one or more bytes:

```asm
msg: DB 'A', 'B', 0x00
```

#### `DW`

Define 16-bit words, likely little-endian unless the project decides otherwise:

```asm
table: DW 0x1234, 0x00FF
```

#### `ASCII`

Emit raw string bytes without terminator:

```asm
msg: ASCII "HELLO"
```

#### `ASCIIZ`

Emit string bytes followed by zero:

```asm
msg: ASCIIZ "HELLO"
```

Notes:

- These directives are standard in many assemblers.
- They are the natural way to describe lookup tables, strings, banners, and test vectors.
- Labels should resolve to the start address of the emitted data block.

### 4. Repetition

Add a repeat block for padding, lookup tables, and test patterns.

Suggested syntax:

```asm
.repeat 16 {
    nop
}
```

Future optional support:

```asm
.repeat 8 i {
    db i
}
```

Status:

- Implemented
- Supports nested `.repeat` blocks
- Repeat counts use integer expressions
- Current syntax requires `{` on the `.repeat` line and a standalone `}` line

### 5. Built-in Helper Functions

Add helper functions for readability:

```asm
LOW(expr)
HIGH(expr)
BYTE0(expr)
BYTE1(expr)
BITS(expr, hi, lo)
```

Examples:

```asm
LDI LOW(@label)
LDI HIGH(@label)
LDL RA, BITS(@label, 4, 0)
LDH RA, BITS(@label, 7, 5)
```

These should coexist with the current slice syntax:

```asm
@label[7:0]
@label[15:8]
@label[4:0]
@label[7:5]
```

Status:

- Implemented
- Supported helpers:
  - `LOW(x)`
  - `HIGH(x)`
  - `BYTE0(x)`
  - `BYTE1(x)`
  - `BITS(x, hi, lo)`
- Supported in both constant expressions and normal operands

### 6. Location Control

Add directives such as:

```asm
.org 0x100
.align 16
.fill 32, 0x00
```

Why this matters:

- force code/data to start at a specific address
- place lookup tables at fixed boundaries
- create ROM headers
- align performance-critical or hardware-visible tables
- avoid manually writing dozens of `NOP`s just to hit an address boundary

Status:

- Implemented
- Supported directives:
  - `.fill count[, byte]`
  - `.org address[, byte]`
  - `.align boundary[, byte]`
- Default fill byte is `0x00`

### 7. Conditional Assembly

Add preprocessor-like control:

```asm
.if FPGA
    ; FPGA-specific code
.else
    ; breadboard-specific code
.endif
```

Possible forms:

```asm
.define FPGA 1
.if FPGA
.if DEBUG
.if LOW(@label) == 0
```

This is especially useful for:

- FPGA vs breadboard builds
- debug UART code
- optional test instrumentation
- feature-gated macros

Status:

- Implemented
- Supported directives:
  - `.define NAME expr`
  - `.if expr`
  - `.else`
  - `.endif`
- Nested conditionals are supported

### 8. Include Files

Add:

```asm
.include "uart.inc"
```

Use cases:

- shared memory-map constants
- reusable macros
- string/data tables
- common startup code

This should be considered a high-priority feature.

Status:

- Implemented
- Quoted include paths are resolved relative to the file that contains the directive
- Include expansion happens before constant extraction and label resolution
- Recursive include chains are rejected

### 9. Strings and Character Support

Current character literal support should be extended consistently across:

- `EQU`
- immediates
- `DB`
- `ASCII`
- `ASCIIZ`
- macro parameters

Desired examples:

```asm
EQU END_CHAR '\0'
LDI 'A'
PUSHI '\n'
DB 'O', 'K', '\n', '\0'
ASCII "HELLO\n"
```

### 10. Listing / Debug Output

Emit an optional human-readable listing file during assembly.

Example command:

```bash
python main.py assemble program.asm output.txt --listing program.lst
```

Useful contents:

- final address
- emitted bytes
- source file and source line number
- original source text

Status:

- Implemented
- Supported through `assemble ... --listing file.lst`
- Current output is source-oriented and shows final emitted bytes for each source line

### 11. Selected Function Imports

Provide a function-library import path that is distinct from textual `.include`.

Example:

```asm
.import "../lib/math.asm" mul_func, square_func
```

Library file structure:

```asm
.export mul_func
.func
mul_func:
    ...
    ret
.endfunc
```

Behavior:

- only selected exported functions are imported
- imported functions are appended after the main source
- imported files may still use `.include`
- duplicate imports are emitted only once

Status:

- Implemented
- Uses `.export`, `.func`, `.endfunc`, and `.import`

## Proposed Priority Order

### Phase 1

- `JMPA`
- `RET`
- `PUSHI`

### Phase 2

- `DB`
- `DW`
- `ASCII`
- `ASCIIZ`
- helper functions like `LOW/HIGH/BITS`

### Phase 3

- `.repeat`
- `.org`
- `.align`
- `.fill`

### Phase 4

- conditional assembly
- richer stack-return syntax
- advanced macro parameterization

## Suggested Syntax Decisions

### Temporary register selection

Use a compact suffix form:

```asm
CALL target :RA
CALL target :RD
JMPA target :RA
JMPA target :RD
PUSHI #65 :RA
PUSHI #65 :RD
PUSHSTR "HELLO" :RA
PUSHSTR "HELLO" :RD
```

Rationale:

- easy to read
- easy to parse
- keeps the primary operand first
- maps naturally onto the register-choice use case

### Return source selection

Use:

```asm
RET
RET :STACK
```

If more flexibility is needed later:

```asm
RET :STACK:RB
```

## Risks and Design Notes

- Pseudoinstructions that optimize away high-byte loads may change code size depending on label value.
- That behavior is useful, but it must be documented and tested carefully.
- Directives like `.org` and `.include` require a more explicit assembly pass model.
- Conditional assembly and macros will likely benefit from a pre-expansion stage before normal parsing.
- Data directives must define how code and data share the same address space.

## Recommended Next Step

Implement Phase 1 first:

`.include`, `CALL`, `JMPA`, `RET`, and `PUSHI` are already implemented. The remaining items above provide the biggest productivity gain with the smallest conceptual jump from the current assembler.
