# ArniComp Assembler - Update Summary

## Overview

The ArniComp assembler has been completely rewritten to support the new ISA (Instruction Set Architecture) with clean code principles, comprehensive validation, and a modern CLI interface.

## Changes Made

### 1. ISA Configuration (`config.json`)
- **New Registers**: RA, RD, RB
- **Destinations**: RA, RD, RB, PRL, PRH, MARL, MARH, M
- **Sources**: RA, RD, RB, ACC, PCL, PCH, M
- **Complete instruction encodings** for all operations

### 2. Core Assembler (`AssemblyHelper.py`)
- **Complete rewrite** with clean code principles
- **Modular design** with `InstructionEncoder` class
- **Comprehensive validation**:
  - MOV restrictions (no same-register moves)
  - NOT source restrictions (RA, RB, ACC, RD, M only)
  - XOR source restrictions (RA, RB, RD, ACC, M only)
  - CMP source restrictions (RA, M, ACC only)
- **EQU keyword** support for constants
- **Improved error messages** with line numbers and context

### 3. Command-Line Interface (`main.py`)
- **Modern CLI** with clear command structure
- **Detailed output**:
  - List of defined labels with addresses
  - List of defined constants with values
  - Assembly statistics
- **Help system** with examples
- **Multiple commands**: assemble, disassemble, createbin, load, verify

### 4. Syntax Improvements
- **Clear prefix rules**:
  - `#` → Direct numbers only (`LDI #31`, `ADDI #7`)
  - `$` → Constants only (`LDI $MAX`)
  - `@` → Labels only (`LDI @loop`)
  - **No combinations** allowed (`#$`, `#@`, etc.)

## File Structure

```
assembler/
├── main.py                    # CLI interface
├── README.md                  # Detailed documentation
├── QUICK_REFERENCE.md         # Quick reference guide
├── UPDATE_SUMMARY.md          # This file
├── config/
│   └── config.json            # ISA definitions
├── modules/
│   ├── AssemblyHelper.py      # Core assembler logic
│   └── EepromLoader.py        # EEPROM loading utilities
└── examples/
    ├── simple_counter.asm     # Simple counter example
    └── comprehensive_test.asm # Comprehensive test suite
```

## Usage Examples

### Basic Assembly
```bash
python3 main.py assemble program.asm
```

### With Custom Output
```bash
python3 main.py assemble program.asm output.txt
```

### Disassemble
```bash
python3 main.py disassemble binary.txt program.asm
```

### Create Binary File
```bash
python3 main.py createbin machine_code.txt program.bin
```

### Load to EEPROM
```bash
python3 main.py load program.bin
```

### All-in-One
```bash
python3 main.py loadasm program.asm
```

## Syntax Examples

### Correct Usage ✅
```assembly
; Constants
equ MAX 100
equ ADDR 0x20

; Labels
start:
    LDI #31          ; # for direct numbers
    LDI $MAX         ; $ for constants
    LDI @start       ; @ for labels
    MOV RD, RA       ; Different registers OK
```

### Incorrect Usage ❌
```assembly
LDI #$MAX        ; ERROR: Don't combine # and $
LDI #@start      ; ERROR: Don't combine # and @
MOV RA, RA       ; ERROR: Forbidden same-register MOV
LDI #200         ; ERROR: Max is 127 (7-bit)
ADDI #8          ; ERROR: Max is 7 (3-bit)
NOT PCL          ; ERROR: NOT doesn't support PCL
```

## Test Results

All test programs assemble successfully:

| Program | Instructions | Labels | Constants | Status |
|---------|-------------|--------|-----------|--------|
| test_program.asm | 31 | 3 | 3 | ✅ Pass |
| simple_counter.asm | 11 | 2 | 1 | ✅ Pass |
| comprehensive_test.asm | 65 | 9 | 3 | ✅ Pass |

## Validation Features

### MOV Instruction
- ✅ Validates source and destination registers
- ✅ Prevents forbidden combinations (RA→RA, RD→RD, RB→RB, M→M)
- ✅ Checks register types (source vs destination)

### Arithmetic Instructions
- ✅ ADD, SUB, ADC, SBC, AND support all sources
- ✅ Immediate operations (ADDI, SUBI) validate 3-bit range (0-7)

### Logical Instructions
- ✅ XOR validates allowed sources (RA, RB, RD, ACC, M)
- ✅ NOT validates allowed sources (RA, RB, ACC, RD, M)

### Comparison
- ✅ CMP validates allowed sources (RA, M, ACC only)

### Load Immediate
- ✅ LDI validates 7-bit range (0-127)

## Error Handling

The assembler provides clear, detailed error messages:

```
Assembly error: Error on line 5 ('MOV RA, RA'): 
  MOV RA, RA is forbidden (same source and destination)

Assembly error: Error on line 10 ('LDI #200'): 
  LDI immediate value 200 out of range (0-127)

Assembly error: Error on line 15 ('NOT PCL'): 
  NOT instruction only supports ['RA', 'RB', 'ACC', 'RD', 'M'], got PCL
```

## Instruction Set Summary

### Data Transfer
- `LDI #imm7` - Load immediate (0-127)
- `MOV dest, src` - Move data

### Arithmetic
- `ADD src` - Add
- `SUB src` - Subtract
- `ADC src` - Add with carry
- `SBC src` - Subtract with carry
- `ADDI #imm3` - Add immediate (0-7)
- `SUBI #imm3` - Subtract immediate (0-7)

### Logical
- `AND src` - Bitwise AND
- `XOR src` - Bitwise XOR
- `NOT src` - Bitwise NOT

### Comparison & Jumps
- `CMP src` - Compare
- `JMP` - Unconditional jump
- `JEQ` - Jump if equal
- `JGT` - Jump if greater
- `JLT` - Jump if less than
- `JGE` - Jump if greater or equal
- `JLE` - Jump if less or equal
- `JNE` - Jump if not equal
- `JC` - Jump if carry

### Special
- `NOP` - No operation
- `HLT` - Halt
- `SMSBRA` - Set MSB of RA
- `INX` - Increment MARL

## Next Steps

The assembler is ready for use! Suggested next steps:

1. ✅ Test with real programs
2. ✅ Verify binary output with emulator
3. ✅ Load to hardware and test
4. 🔄 Add more example programs as needed
5. 🔄 Implement disassembler improvements (optional)

## Version History

- **v2.0** (October 2025) - Complete rewrite for new ISA
  - Clean code architecture
  - Comprehensive validation
  - Modern CLI interface
  - Full documentation

- **v1.0** - Original implementation (deprecated)

## Author

sonmezarda

## Repository

ArniComp-Support-Package
Branch: main
