# Arnicomp Support Package

**Arnicomp Support Package** is a collection of software tools built to support **Arnicomp**, a custom-designed 8-bit breadboard computer.  
Rather than focusing on a single component, this repository brings together all auxiliary tooling required to assemble, simulate, debug, and work with the Arnicomp architecture.

This repository is **in active development**.  
S
---
## Breadboard Computer (ISA Version 2)
<img width="1536" height="2048" alt="image" src="https://github.com/user-attachments/assets/0b65c46d-36dc-4746-bf03-d5ff110acf0a" />
<img width="1536" height="2048" alt="image" src="https://github.com/user-attachments/assets/8fc7ed4a-29ec-4153-b5ca-6e0e7b6d5184" />



---
## Digital Circuit Simulation Design
<img width="643" height="904" alt="Layout of internal architecture" src="https://github.com/user-attachments/assets/afdabe26-a776-4f26-8def-c8c8c2e29895" />

<img width="1069" height="913" alt="Basic test circuit with seven segment display and buttons" src="https://github.com/user-attachments/assets/7350a02a-0452-49e5-8a74-cb2c2d1478dd" />

---
## Repository Contents

### 📁 `/digital-sim`
- **Digital.exe simulation models**
- Logic-level simulation files used to validate the Arnicomp hardware design
- Allows inspection of signal flow, control logic, and timing behavior

---

### 📁 `/assembler`
- **Fully functional Arnicomp assembler**
- Converts Arnicomp assembly language into executable machine code
- Features:
  - Label resolution
  - Constant definitions
  - Complete support for the latest ISA
- This directory contains the **current and stable** assembler implementation

#### Instruction Set:
- Current (Newest ISA :) )
<img width="1287" height="624" alt="Newest ISA Complete" src="https://github.com/user-attachments/assets/38aed79a-826f-40c1-82c9-23932f265917" />
<img width="531" height="198" alt="Newest ISA Select Bits" src="https://github.com/user-attachments/assets/a5eacc60-ad09-4d24-bd98-8c8f25a2df01" />

- Old ISA
<img width="903" height="295" alt="Old ISA " src="https://github.com/user-attachments/assets/8401d026-5592-43dc-8bdc-46becc4a0fec" />

---

### 📁 `/emulator`
- **Arnicomp CPU emulator**
- Emulates the processor cycle-by-cycle with hardware-accurate behavior
- Executes assembled machine code exactly as the physical CPU would
- Primarily used for:
  - Debugging programs
  - Verifying instruction semantics
  - Testing assembler output without physical hardware

---

### 📁 `/emulator_ui`
- **Graphical user interface for the emulator**
- Designed to work directly with `/emulator`
- Enables:
  - Loading and editing assembly files
  - Step-by-step execution
  - Breakpoints
  - Register and flag inspection
- The UI was largely **AI-assisted**, as frontend development is not the primary focus of the project

---

### 📁 `/compiler`
- **Incomplete compiler prototype**
- Not finished in this repository
- Compiler development has continued in a **separate repository**, restarted from scratch
- This directory remains for historical reference only

---

### 📁 `/vscode-arnicomp`
- **Visual Studio Code extension**
- Provides syntax highlighting for the Arnicomp assembly language
- Makes writing and reading assembly code significantly easier

---

## Development Notes

- The project went through **two major instruction set and architecture revisions** during development
- As a result, some directory structure and legacy files may appear inconsistent
- Older designs were intentionally preserved to:
  - Track architectural evolution
  - Avoid breaking working tooling
  - Serve as reference during ISA redesigns

---

## AI Usage Disclaimer

- Except for the **emulator UI**, AI-generated code usage is minimal
- Core components such as:
  - Assembler
  - Emulator
  - ISA design
  
  were written and verified manually
- AI assistance was mainly used for:
  - UI layout generation
  - Boilerplate frontend code
  - Minor refactors and documentation drafts

---

## ISA Evolution (2025 Redesign)

During development, the original opcode/argcode-based instruction format was replaced with the current **final 8-bit ISA** used by the assembler and Verilog implementation.

Key characteristics of the current ISA include:
- `LDL` / `LDH` split byte construction for `RA` and `RD`
- unified `MOV` encoding (`10 ddd sss`)
- source-side `ZERO`, `LRL`, and `LRH` bus options
- arithmetic family using `RD` as the left operand:
  - `ADD`, `ADDI`, `ADC`
  - `SUB`, `SUBI`, `SBC`
  - `CMP`
- logical operations:
  - `XOR`, `AND`, `NOT`
- stack operations:
  - `PUSH`, `POP`
- MAR update operations:
  - `INC #1/#2`
  - `DEC #1/#2`
- jump family based on `Z/N/C/V` flags:
  - `JEQ`, `JNE`, `JCS`, `JCC`, `JMI`, `JVS`, `JLT`, `JMP`
  - `JGT` as the dedicated extra opcode
  - `JAL` for link-and-jump through `PRH:PRL`
- `LRL` / `LRH` replacing the older direct `PC` readback model

Assembler-side productivity features now include pseudoinstructions such as:
- `LDI`
- `CALL`
- `JMPA`
- `RET`
- `PUSHI`
- `PUSHSTR`

The assembler README documents the current split between:
- real ISA instructions
- assembler pseudoinstructions/macros
- aliases

Legacy documentation remains in `arnicomp_details.txt` for historical context.

---

## Current Status

| Component        | Status        |
|------------------|--------------|
| Assembler        | ✅ Complete |
| Emulator         | ✅ Complete |
| Emulator UI      | ✅ Complete |
| VS Code Extension| ✅ Complete |
| Compiler         | 🚧 Continued in separate repo |

---

## License & Contributions

This project is primarily intended for **educational, experimental, and personal hardware development** purposes.

Feedback on:
- ISA design
- Emulator accuracy
- Tooling structure

is always welcome.

---

> Arnicomp is a long-term exploration of CPU design, tooling, and low-level software — not just a single assembler.
