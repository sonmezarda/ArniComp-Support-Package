# ArniComp Assembly Quick Reference

## Syntax Rules

### Prefixes
- **`#`** - Direct numbers: `LDI #31`, `ADDI #7`, `LDI #0x10`, `LDI #0b0101`
- **`$`** - Constants: `LDI $COUNTER`, `CMP $MAX`
- **`@`** - Labels: `LDI @loop`, `LDI @start`

**IMPORTANT**: Do NOT combine prefixes! No `#$`, `#@`, `$#`, or `@#`!

### Comments and Definitions
```assembly
; This is a comment

equ CONSTANT_NAME value
equ MAX 100
equ ADDR 0x20

label:
    instruction
```

## Registers

| Register | Description | Type |
|----------|-------------|------|
| RA | General purpose | Source & Dest |
| RD | General purpose (ALU input) | Source & Dest |
| RB | General purpose | Source & Dest |
| ACC | Accumulator | Source only |
| PCL | Program counter low | Source only |
| PCH | Program counter high | Source only |
| PRL | Program register low | Dest only |
| PRH | Program register high | Dest only |
| MARL | Memory address low | Dest only |
| MARH | Memory address high | Dest only |
| M | Memory[MARH:MARL] | Source & Dest |

## Instructions

### Data Transfer
```assembly
LDI #value          ; Load immediate to RA (0-127)
MOV dest, src       ; Move from src to dest
```

**MOV Restrictions**:
- Cannot: `MOV RA, RA` / `MOV RD, RD` / `MOV RB, RB` / `MOV M, M`

### Arithmetic
```assembly
ADD src             ; ACC = RD + src
SUB src             ; ACC = RD - src
ADC src             ; ACC = RD + src + carry
SBC src             ; ACC = RD - src - carry
ADDI #value         ; ACC = ACC + value (0-7)
SUBI #value         ; ACC = ACC - value (0-7)
```

**All sources allowed**: RA, RD, RB, ACC, PCL, PCH, M

### Logical
```assembly
AND src             ; ACC = RD & src
XOR src             ; ACC = RD ^ src (RA, RB, RD, ACC, M only)
NOT src             ; ACC = ~src (RA, RB, ACC, RD, M only)
```

### Comparison
```assembly
CMP src             ; Compare src with RD (RA, M, ACC only)
```

### Jumps
```assembly
JMP                 ; Unconditional jump
JEQ                 ; Jump if equal (zero flag)
JGT                 ; Jump if greater than
JLT                 ; Jump if less than
JGE                 ; Jump if greater or equal
JLE                 ; Jump if less or equal
JNE                 ; Jump if not equal
JC                  ; Jump if carry
```

**Jump Usage**:
```assembly
; Load target address to PRL first
LDI @target         ; Load target address
MOV PRL, RA         ; Set program register
JMP                 ; Execute jump

target:
    ; code here
```

### Special
```assembly
NOP                 ; No operation
HLT                 ; Halt processor
SMSBRA              ; Set MSB of RA to 1
INX                 ; Increment MARL
```

## Common Patterns

### Counting Loop
```assembly
equ MAX 10

start:
    LDI #0
    MOV RD, RA
    
loop:
    ADDI #1
    MOV RD, ACC
    LDI $MAX
    CMP RA
    JLT             ; Jump if still less than MAX
    HLT
    
    LDI @loop
    MOV PRL, RA
    JMP
```

### Memory Access
```assembly
equ ADDR 0x20

    ; Write to memory
    LDI $ADDR
    MOV MARL, RA
    LDI #0
    MOV MARH, RA
    LDI #42
    MOV M, RA
    
    ; Read from memory
    MOV RA, M
```

### Conditional Execution
```assembly
    ; Compare two values
    LDI #10
    MOV RD, RA
    LDI #20
    CMP RA
    JLT             ; Jump if 20 < 10 (false, continues)
    
    ; This executes because jump didn't happen
    HLT
```

## Number Formats

```assembly
#10         ; Decimal
#0x0A       ; Hexadecimal (0-9, A-F)
#0b1010     ; Binary (0-1)
```

## Error Prevention

### ❌ Common Mistakes
```assembly
LDI #$CONST         ; WRONG: don't combine # and $
LDI #@label         ; WRONG: don't combine # and @
MOV RA, RA          ; WRONG: forbidden same-register MOV
LDI #200            ; WRONG: max is 127 (7-bit)
ADDI #8             ; WRONG: max is 7 (3-bit)
NOT PCL             ; WRONG: NOT doesn't support PCL
CMP RD              ; WRONG: CMP only supports RA, M, ACC
```

### ✅ Correct Usage
```assembly
LDI $CONST          ; Correct: $ alone for constants
LDI @label          ; Correct: @ alone for labels
MOV RD, RA          ; Correct: different registers
LDI #127            ; Correct: within 0-127
ADDI #7             ; Correct: within 0-7
NOT RA              ; Correct: RA is allowed
CMP RA              ; Correct: RA is allowed
```

## CLI Commands

```bash
# Assemble
python3 main.py assemble input.asm [output.txt]

# Disassemble
python3 main.py disassemble input.txt [output.asm]

# Create binary
python3 main.py createbin input.txt [output.bin]

# Load to EEPROM
python3 main.py load program.bin

# All-in-one
python3 main.py loadasm program.asm

# Help
python3 main.py help
```
