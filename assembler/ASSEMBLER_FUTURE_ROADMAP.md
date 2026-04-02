# Assembler Future Roadmap

This document captures proposed quality-of-life and power-user features for the ArniComp assembler after the final ISA migration.

## Goals

- Reduce repetitive handwritten boilerplate for calls, jumps, stack usage, and string output.
- Keep low-level control available for optimized hand-written assembly.
- Add common assembler conveniences without hiding machine behavior.
- Preserve explicitness where instruction count or register choice matters.

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
POP PRL      ; low byte
POP PRH      ; high byte
JMP
```

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

## Proposed Priority Order

### Phase 1

- `CALL`
- `JMPA`
- `RET`
- `PUSHI`
- `.include`

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

1. `.include`
2. `CALL`
3. `JMPA`
4. `RET`
5. `PUSHI`

These provide the biggest productivity gain with the smallest conceptual jump from the current assembler.
