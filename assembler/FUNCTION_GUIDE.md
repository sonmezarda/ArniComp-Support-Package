# ArniComp Function Guide

This document defines a practical function-calling convention for ArniComp assembly.

The goal is not to imitate a large-system ABI. The goal is to make hand-written routines consistent, easy to reuse, and safe to compose with the current ISA and assembler pseudoinstructions.

## Recommended Calling Convention

### Registers

- `RB`
  - primary input register
  - primary return register
  - use this for most 8-bit single-argument functions
- `RD`
  - secondary input register
  - optional high-byte return register for 16-bit results
- `RA`
  - scratch register
  - not preserved
  - often clobbered by `LDI`, address-loading pseudoinstructions, and helper code

### Return values

- 8-bit return value:
  - `RB`
- 16-bit return value:
  - `RD` = low byte
  - `RB` = high byte

### Extra arguments

- first argument: `RB`
- second argument: `RD`
- further arguments: stack or scratch memory

### Multi-byte register pairs

For 16-bit values stored in registers, use little-endian register order:

- `RD` = low byte
- `RB` = high byte

This is recommended because:

- the ALU naturally consumes `RD`
- low-byte arithmetic usually happens first
- `ADD` then `ADC` chains become shorter and cheaper

Example:

```assembly
; 16-bit value 0x1234
ldi #0x34
mov rd, ra
ldi #0x12
mov rb, ra
```

## Register Preservation Rules

### Callee-clobbered

These may be modified by the function unless the function explicitly documents otherwise:

- `RA`
- `RB`
- `RD`
- `ACC`
- flags (`Z/N/C/V`)
- `MARL`
- `MARH`
- `PRL`
- `PRH`

### Caller responsibility

If the caller needs any of these values after the call, the caller must preserve them before calling:

- `RA`
- `RD`
- `MARL`
- `MARH`
- flags

### Callee responsibility

The callee should only promise to preserve something if that is part of the routine's documented contract.

Default assumption:

- functions do **not** preserve `RA`
- functions do **not** preserve `RD`
- functions return their main result in `RB`
- for 16-bit returns, functions should return `RD` low and `RB` high

This is intentional. `RA` and `RD` are both heavily used by the current ISA and by assembler-generated code.

## Why `RB` Is The Preferred 8-bit Argument / Return Register

- `RA` is frequently overwritten by `LDI`, `CALL`, `JMPA`, target-taking jumps, and other helper patterns
- `RD` is the ALU's left-hand operand and is frequently used for compare/arithmetic setup
- `RB` is the cleanest general-purpose choice for stable function input/output

That makes these patterns natural:

```assembly
; in : RB = ascii
; out: RB = digit
ascii_to_number_func:
    ...
    ret
```

```assembly
; in : RB = value
; out: RB = ascii
number_to_ascii_func:
    ...
    ret
```

```assembly
; in : RB = a, RD = b
; out: RB = a*b (low 8 bits)
mul_func:
    ...
    ret
```

For 16-bit values, the recommended pair is still:

- `RD` = low byte
- `RB` = high byte

So a 16-bit add routine is naturally documented like this:

```assembly
; in :
;   RD = a_lo
;   RB = a_hi
; out:
;   RD = sum_lo
;   RB = sum_hi
add_u16_func:
    ...
    ret
```

## Nested Calls And Recursion

`CALL` uses `JAL`, and `JAL` updates `LRL/LRH`.

That means:

- leaf functions can usually just `RET`
- non-leaf functions must preserve their own return address before making another `CALL`
- recursive functions must also preserve the current return address before the recursive call

If a function calls another function and then still wants to return to its own caller, it should save `LRL/LRH` first.

Example stack-friendly pattern:

```assembly
; save current return address
push lrl
push lrh

call some_other_func :RD

; later return through saved address
ret :stack
```

Important note:

- `RET :STACK` expects the return address on the stack as:
  - low byte pushed first
  - high byte pushed second

That is exactly why the example pushes `LRL` before `LRH`.

## Pseudoinstruction Temp Register Hazards

Some assembler pseudoinstructions load temporary addresses through a register before branching:

- `CALL target`
- `JMPA target`
- target-taking jumps such as `JEQ done`

By default these use `RA` as the temporary register. Some forms also allow `:RD`.

That means:

- `CALL func` may clobber `RA`
- `CALL func :RD` may clobber `RD`
- target-taking jump pseudoinstructions follow the same rule

Practical rule:

- do not choose a temp-register form that overwrites a live function argument

Example:

```assembly
; mul_u8 expects:
;   RB = a
;   RD = b

ldi #6
mov rb, ra
ldi #7
mov rd, ra

call mul_u8      ; good, default temp is RA
; call mul_u8 :RD ; bad, would overwrite b before the call
```

## Scratch Memory Convention

ArniComp code often needs a small global scratch area for:

- extra parameters
- temporary bytes
- 16-bit intermediate values
- helper routines that outgrow register-only code

Recommended include:

```assembly
.include "../includes/function_abi.asm"
```

Recommended scratch page:

- high byte: `0x00`
- address range reserved by convention: `0x0000..0x001F`

Why this default:

- this SoC maps writable data RAM starting at `0x0000`
- using the first scratch page keeps helper code portable across the current examples and FPGA build
- the old `0x0E00` suggestion is not valid on the current memory map

This area is not automatic stack frame storage. It is a shared scratch page.

That means:

- it is simple and cheap
- it is fine for non-reentrant helper code
- recursive code must use it carefully
- nested routines should document which scratch slots they use
- stack use is perfectly valid when it simplifies the routine, but core math helpers should avoid stack/scratch traffic when a register-only implementation is practical

Library note:

- the current `.import` system does not auto-resolve function-to-function dependencies
- exported library routines should therefore prefer to be self-contained when practical
- if a routine intentionally calls another imported helper, the caller must import both

## Included Scratch Symbols

The scratch include defines:

- `F_TMP_BASE_H`
- `F_T0_L .. F_T7_L`
- `F_W0_LO_L / F_W0_HI_L`
- `F_W1_LO_L / F_W1_HI_L`
- `F_A2_L .. F_A5_L`

Suggested usage:

```assembly
ldi $F_TMP_BASE_H
mov marh, ra

ldi $F_T0_L
mov marl, ra
mov m, rb
```

## Suggested Function Comment Header

Use a short header like this:

```assembly
; mul_func
; in :
;   RB = a
;   RD = b
; out:
;   RB = a*b (low 8 bits)
; clobbers:
;   RA, RD, ACC, flags
; scratch:
;   none
```

Or, when scratch memory is used:

```assembly
; parse_u8_func
; in :
;   RB = first digit
; out:
;   RB = parsed value
; clobbers:
;   RA, RD, ACC, flags, MARL, MARH
; scratch:
;   F_T0_L
;   F_W0_LO_L
;   F_W0_HI_L
```

Example 16-bit header:

```assembly
; add_u16_scratch
; in :
;   RD = a_lo
;   RB = a_hi
;   [F_TMP_BASE_H:F_W0_LO_L] = b_lo
;   [F_TMP_BASE_H:F_W0_HI_L] = b_hi
; out:
;   RD = sum_lo
;   RB = sum_hi
; clobbers:
;   RA, ACC, flags, MARL, MARH
; scratch:
;   none
```

## Practical Summary

- use `RB` for the primary argument and primary return
- use `RD` for the second argument
- use `RD` low / `RB` high for 16-bit register pairs and 16-bit returns
- treat `RA` as volatile scratch
- assume `RD` is caller-saved unless the function contract says otherwise
- save `LRL/LRH` before nested `CALL`s
- use the shared scratch page for extra state
- be careful with recursion, because both `LR` and scratch memory must be handled deliberately
