# ArniComp Compiler

A high-level language compiler for the ArniComp custom ISA architecture.

## Features

- **Variable Management**: Automatic memory allocation for byte, byte arrays, and uint16 types
- **Expression Evaluation**: Arithmetic operations (+, -, &) with register optimization
- **Control Flow**: if/elif/else statements and while loops
- **Memory Access**: Direct memory access via pointers (*address)
- **Array Support**: Constant and variable array indexing
- **Register Optimization**: Smart register allocation and caching
- **Preprocessor**: Macro definitions with #define
- **Direct Assembly**: Insert raw assembly with dasm/endasm blocks

## Installation

```bash
cd compiler
# No additional dependencies required beyond Python 3.10+
```

## Quick Start

### Basic Compilation

```bash
# Compile a source file
python main.py compile program.arn

# Specify output file
python main.py compile program.arn -o output.asm

# Enable verbose mode
python main.py compile program.arn -v
```

### Memory Configuration

```bash
# Custom memory layout
python main.py compile program.arn \
    --var-start 0x0000 \
    --var-end 0x0400 \
    --stack-start 0x0400 \
    --stack-size 512

# Save configuration for future use
python main.py config \
    --var-start 0x0000 \
    --var-end 0x0400 \
    --save
```

### Configuration Management

```bash
# Show current configuration
python main.py config --show

# Load custom config file
python main.py compile program.arn -c custom.config.json

# Reset to defaults
python main.py config --reset --save
```

### Validation

```bash
# Validate syntax without compilation
python main.py validate program.arn
```

### Information

```bash
# Show compiler capabilities
python main.py info
```

## Command Reference

### Compile Command

```
python main.py compile <input.arn> [options]

Options:
  -o, --output FILE          Output file (default: input.asm)
  -f, --format {asm,hex,bin} Output format (default: asm)
  -v, --verbose              Enable verbose output (show compilation steps)
  -d, --debug                Enable debug mode (detailed logging of all operations)
  --no-stats                 Disable statistics output
  -O, --optimize LEVEL       Optimization level (0-2)

Debug Levels:
  Normal:    Only show errors and final output
  Verbose:   Show compilation progress and statistics
  Debug:     Show detailed internal operations (parsing, register allocation, etc.)

Memory Configuration:
  --var-start ADDR           Variable memory start (hex: 0x0000)
  --var-end ADDR             Variable memory end (hex: 0x0200)
  --stack-start ADDR         Stack start address (hex: 0x0100)
  --stack-size BYTES         Stack size in bytes (default: 256)
  --memory-size BYTES        Total memory size (default: 65536)
  --comment-char CHAR        Comment character (default: //)
```

### Config Command

```
python main.py config [options]

Options:
  --show                     Display current configuration
  --save                     Save configuration to file
  --reset                    Reset to default configuration
  --var-start, --var-end     Memory configuration (same as compile)
  --stack-start, --stack-size
  --memory-size, --comment-char
```

## Language Syntax

### Variables

```c
// Byte variables
byte x;
byte y = 10;

// Byte arrays
byte[5] arr;
byte[10] buffer;

// 16-bit unsigned integers
uint16 counter;
uint16 address = 0x1234;
```

### Expressions

```c
byte a = 5;
byte b = 10;
byte c = a + b;       // Addition
byte d = b - a;       // Subtraction
byte e = a & b;       // Bitwise AND
```

### Control Flow

```c
// If statements
if a == 5
    x = 1;
endif

// If-elif-else
if a > b
    x = 1;
elif a < b
    x = 2;
else
    x = 3;
endif

// While loops
while x < 10
    x = x + 1;
endwhile
```

### Arrays

```c
byte[5] arr;

// Constant index
arr[0] = 5;
arr[1] = 10;

// Variable index
byte i = 2;
arr[i] = 15;
```

### Memory Access

```c
// Direct memory write
*0x1234 = 42;

// Using variables
uint16 addr = 0x1234;
byte value = 42;
```

### Preprocessor

```c
// Define constants
#define SCREEN_ADDR 0xFF00
#define MAX_COUNT 100

// Use in code
*SCREEN_ADDR = 0x7F;

byte x;
while x < MAX_COUNT
    x = x + 1;
endwhile
```

### Direct Assembly

```c
dasm
    ldi #127
    mov rd, ra
    add rd
endasm
```

## Configuration File Format

The `compiler.config.json` file uses JSON format:

```json
{
    "comment_char": "//",
    "variable_start_addr": 0,
    "variable_end_addr": 512,
    "stack_start_addr": 256,
    "stack_size": 256,
    "memory_size": 65536,
    "output_format": "asm",
    "optimization_level": 0,
    "debug_mode": false,
    "verbose": false,
    "show_stats": true
}
```

## Memory Layout

Default memory map:

```
0x0000 - 0x0200  Variable Memory (512 bytes)
0x0100 - 0x01FF  Stack Memory (256 bytes)
0x0200 - 0xFFFF  Program/Data Memory
```

The variable and stack regions can be configured via command-line flags or config file.

## Examples

### Example 1: Counter Program

```c
// count_test.arn
#define MAX 10

byte counter;
counter = 0;

while counter < MAX
    counter = counter + 1;
endwhile
```

Compile:
```bash
python main.py compile files/count_test.arn -v
```

### Example 2: Array Manipulation

```c
// array_test.arn
byte[5] data;
byte i;

// Initialize array
i = 0;
while i < 5
    data[i] = i;
    i = i + 1;
endwhile
```

### Example 3: Custom Memory Layout

```c
// large_program.arn with more variable space
```

Compile with custom config:
```bash
python main.py compile large_program.arn \
    --var-start 0x0000 \
    --var-end 0x0800 \
    --stack-start 0x0800 \
    --stack-size 512 \
    -v
```

## Statistics Output

The compiler provides detailed statistics after compilation:

```
=== Compilation Statistics ===
  Input file size:          245 bytes
  Output file size:         1024 bytes
  Assembly instructions:    128
  Variables allocated:      5
  Memory used:              12/512 bytes (2.3%)
  Stack size:               256 bytes

  Instruction breakdown:
    LDI      :   32 ( 25.0%)
    MOV      :   28 ( 21.9%)
    ADD      :   18 ( 14.1%)
    ...
```

## Troubleshooting

### Validation Errors

Use `validate` command to check syntax before compilation:

```bash
python main.py validate program.arn
```

### Debug Mode

Enable debug mode for detailed error messages:

```bash
python main.py compile program.arn -d
```

### Memory Issues

If you encounter "Not enough memory" errors:

1. Increase variable memory range: `--var-end 0x0400`
2. Check for memory leaks (variables not freed)
3. Review variable allocation with verbose mode: `-v`

## Development

The compiler is modular and extensible:

- `CompilerHelper.py`: Main compilation logic
- `VariableManager.py`: Memory allocation
- `RegisterManager.py`: Register allocation
- `LabelManager.py`: Label and jump management
- `ConditionHelper.py`: Control flow structures
- `Commands.py`: Command parsing
- `CompilerStaticMethods.py`: Utility functions

## License

Part of the ArniComp custom ISA project.
