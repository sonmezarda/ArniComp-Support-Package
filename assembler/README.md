# ArniComp Assembler

A clean, modern assembler for the ArniComp custom ISA architecture with support for the latest instruction set.

## Features

- **Complete ISA Support**: All instructions including MOV, arithmetic, logical, jumps, and special instructions
- **Constants**: Define constants using `equ` keyword
- **Labels**: Support for labels and label references
- **Multiple Number Formats**: Decimal, hexadecimal (0x), and binary (0b)
- **Validation**: Comprehensive error checking for instruction restrictions
- **CLI Interface**: Easy-to-use command-line interface
- **Disassembler**: Convert binary back to assembly

## Architecture Overview

### Registers
- **RA, RD, RB**: General purpose registers (8-bit)
- **ACC**: Accumulator (8-bit)
- **PCL, PCH**: Program counter low/high (8-bit each)
- **PRL, PRH**: Program register low/high (8-bit each)
- **MARL, MARH**: Memory address register low/high (8-bit each)
- **M**: Memory at address [MARH:MARL]

### Instruction Set

#### Data Movement
- `LDI #imm7` - Load immediate to RA (0-127)
- `MOV dest, src` - Move from source to destination
  - Sources: RA, RD, RB, ACC, PCL, PCH, M
  - Destinations: RA, RD, RB, PRL, PRH, MARL, MARH, M
  - Forbidden: MOV RA,RA / MOV RD,RD / MOV RB,RB / MOV M,M

#### Arithmetic
- `ADD src` - Add source to RD, result in ACC
- `SUB src` - Subtract source from RD, result in ACC
- `ADC src` - Add with carry
- `SBC src` - Subtract with carry
- `ADDI #imm3` - Add immediate (0-7)
- `SUBI #imm3` - Subtract immediate (0-7)

#### Logical
- `AND src` - Bitwise AND
- `XOR src` - Bitwise XOR (allowed: RA, RB, RD, ACC, M)
- `NOT src` - Bitwise NOT (allowed: RA, RB, ACC, RD, M)

#### Comparison & Jumps
- `CMP src` - Compare source with RD (allowed: RA, M, ACC)
- `JMP` - Unconditional jump
- `JEQ` - Jump if equal
- `JGT` - Jump if greater than
- `JLT` - Jump if less than
- `JGE` - Jump if greater or equal
- `JLE` - Jump if less or equal
- `JNE` - Jump if not equal
- `JC` - Jump if carry

#### Special
- `NOP` - No operation
- `HLT` - Halt processor
- `SMSBRA` - Set MSB of RA to 1
- `INX` - Increment MARL

## Usage

### Installation

```bash
cd /path/to/ArniComp-Support-Package/assembler
# No installation needed, just use Python 3
```

### Basic Commands

```bash
# Assemble a program
python3 main.py assemble program.asm output.txt

# Disassemble binary code
python3 main.py disassemble binary.txt output.asm

# Create binary file
python3 main.py createbin machine_code.txt program.bin

# Load to EEPROM
python3 main.py load program.bin

# All-in-one: assemble and load
python3 main.py loadasm program.asm

# Get help
python3 main.py help
```

### Assembly Syntax

```assembly
; Comments start with semicolon

; Define constants
equ CONSTANT_NAME value
equ MAX_COUNT 100
equ START_ADDR 0x00

; Define labels
start:
    LDI #0              ; Load immediate (# for direct numbers)
    MOV RD, RA          ; Move data
    
loop:
    ADDI #1             ; Add immediate
    CMP ACC             ; Compare
    JLT                 ; Conditional jump
    
    ; To jump to a label, load address then jump
    LDI @loop           ; @ for label addresses
    MOV PRL, RA         ; Set program register
    JMP                 ; Execute jump
    
    HLT                 ; Halt

; Use constants with $ prefix (no # needed)
    LDI $MAX_COUNT      ; $ for constants
    LDI $START_ADDR
```

### Number Formats

```assembly
; Direct numbers use # prefix
LDI #10        ; Decimal
LDI #0x0A      ; Hexadecimal
LDI #0b1010    ; Binary

; Constants use $ prefix (no # needed)
equ VALUE 10
LDI $VALUE     ; Correct: $ only

; Labels use @ prefix (no # needed)
label:
    NOP
LDI @label     ; Correct: @ only
```

## Examples

### Example 1: Simple Counter

```assembly
equ MAX 10

start:
    LDI #0
    MOV RD, RA
    
loop:
    ADDI #1
    MOV RD, ACC
    LDI #$MAX
    CMP RA
    JLT
    HLT
    
    LDI #@loop
    MOV PRL, RA
    JMP
```

### Example 2: Memory Operations

```assembly
equ DATA_ADDR 0x20

start:
    ; Set memory address
    LDI $DATA_ADDR      ; Use $ for constants
    MOV MARL, RA
    LDI #0
    MOV MARH, RA
    
    ; Write to memory
    LDI #42             ; Use # for direct numbers
    MOV M, RA
    
    ; Read from memory
    MOV RA, M
    
    HLT
```

## Instruction Encoding

All instructions are 8 bits:

```
Format: IM7 MV A1 A2 J S2 S1 S0

- IM7=1: LDI instruction (7-bit immediate follows)
- IM7=0, MV=1: MOV instruction
- IM7=0, MV=0, A1A2=00: Arithmetic (ADD, SUB, ADC, SBC, AND, XOR)
- IM7=0, MV=0, A1A2=10: Jump instructions
- IM7=0, MV=0, A1A2=11: Immediate arithmetic (ADDI, SUBI)
```

## Error Handling

The assembler provides detailed error messages:

```
Assembly error: Error on line 5 ('MOV RA, RA'): MOV RA, RA is forbidden
Assembly error: Error on line 10 ('LDI #200'): LDI immediate value 200 out of range (0-127)
Assembly error: Error on line 15 ('NOT PCL'): NOT instruction only supports ['RA', 'RB', 'ACC', 'RD', 'M']
```

## Development

### Project Structure

```
assembler/
├── main.py                  # CLI interface
├── modules/
│   ├── AssemblyHelper.py    # Core assembler logic
│   └── EepromLoader.py      # EEPROM loading utilities
├── config/
│   └── config.json          # ISA configuration
├── examples/
│   └── simple_counter.asm   # Example programs
└── README.md                # This file
```

### Adding New Instructions

1. Update `config.json` with instruction details
2. Add encoding method in `InstructionEncoder` class
3. Add parsing in `AssemblyHelper.encode_instruction()`
4. Add disassembly support in `AssemblyHelper.disassemble()`

## License

Part of the ArniComp Support Package project.

## Author

sonmezarda

## Version

2.0 - Complete rewrite for new ISA (October 2025)
