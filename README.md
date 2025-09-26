# Assembler-Arnicomp

This repository is currently under development.

Assembler-Arnicomp is an assembler project designed for a breadboard computer that I have built. The assembler translates assembly code into machine code that runs on the custom hardware. In addition to the assembler, this project will eventually include an emulator and a compiler, both of which are still in progress.

## Digital.exe Simulation Model
<img width="804" height="830" alt="image" src="https://github.com/user-attachments/assets/b10fd851-3feb-4a6f-80e6-096f6f67534e" />

## Project Overview

- **Assembler:** ✅ Fully functional. Converts assembly instructions for the Arnicomp breadboard computer into executable machine code.
- **Emulator:** ✅ Complete and tested. Simulates the ArniComp 8-bit CPU with Harvard Architecture, allowing you to test programs without physical hardware.
- **Compiler:** 🚧 Under development. Will allow higher-level code to be compiled down to Arnicomp assembly.

## Status

- ✅ **Assembler**: Complete with label resolution, constant support, and full instruction set
- ✅ **Emulator**: Complete with interactive debugger, step-by-step execution, and hardware-accurate simulation
- 🚧 **Compiler**: Expression parsing implemented, full compiler in progress

## Getting Started

Documentation and usage examples will be added as the project progresses.

## ISA Evolution (2025 Redesign)

During ongoing development the original opcode/argcode table driven instruction set (separate 4-bit opcode + 3-bit argcode, plus legacy LDR/STR and OUT/IN forms) was replaced with a new leading‑zero class based encoding (Rev 2). This redesign:

- Uses the count of leading zero bits to classify instruction families.
- Introduces combined MOV field encoding (01 ddd sss) instead of source-in-opcode/dest-in-argcode mapping.
- Collapses separate load/store instructions into MOV semantics for memory (ML/MH pseudo registers) and device bus I/O.
- Adds arithmetic family (ADD/SUB/ADC/SBC) and short immediates (ADDI imm3, SUBI imm2).
- Adds logical AND, dual NOP encodings, and a JC (jump on carry) condition.
- Introduces a carry flag (C) with standard add overflow / no‑borrow semantics, while keeping comparator flags EQ/LT/GT.

Legacy docs persisted in `arnicomp_details.txt` were superseded; that file now records the new layout alongside remnants of earlier reference material for historical context.

## AI-Assisted Migration

Porting from the legacy ISA to the new encoding was partially automated using an AI coding assistant. The assistant helped to:

- Rewrite emulator decode/execute logic to match the new instruction classification.
- Update disassembly utilities and create new test suites (encoding, negative cases, carry & jump behavior).
- Draft and update documentation for the revised ISA.

Human review followed each automated change—especially around subtle semantics (e.g., CRA behavior, carry vs borrow, and MOV side‑effects on ML/MH memory operations). Any remaining inconsistencies are tracked for iterative refinement.

If you examine commit history you may see clustered larger diffs corresponding to these assisted refactors; they're intentionally scoped to keep manual verification practical.

## Next Steps

- Expand compiler to exploit new short immediate forms more aggressively.
- Add more exhaustive emulator tests (SBC borrow chains, stress patterns for MOV+memory).
- Provide a migration guide for old assembly source (mapping obsolete mnemonics like STRL/LDRL to new MOV forms).

Contributions and feedback on the new encoding or further tooling are welcome.
