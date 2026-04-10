# ArniComp - Tang Nano 9K FPGA Implementation

## Quick Start

### Option 1: Import Project File (Recommended)
1. Open Gowin IDE (GOWIN FPGA Designer)
2. File → Open Project
3. Select `arnicomp_tang_nano_9k.gprj`
4. All source files will be automatically added

### Option 2: Create New Project Manually
1. File → New → FPGA Design Project
2. Select device: **GW1NR-LV9QN88PC6/I5** (Tang Nano 9K)
3. Add source files in this order:
   - `rtl/pkg/control_pkg.sv` (MUST be first)
   - All files from `rtl/lib/`
   - All files from `rtl/blocks/`
   - All files from `rtl/core/`
   - All files from `rtl/mem/`
   - `rtl/top/arnicomp_top.sv`
   - `rtl/top/tang_nano_9k_top.sv`
4. Add constraint file: `constraints/tang_nano_9k.cst`
5. Set top module: `tang_nano_9k_top`

## Hardware Connections

| Signal | Tang Nano 9K Pin | Description |
|--------|-----------------|-------------|
| clk | 52 | 27MHz crystal oscillator |
| rst_n | 4 | Button S1 (Reset, active low) |
| btn_run | 3 | Button S2 (Run/Step) |
| led[0] | 10 | LED 0 (ACC bit 0) |
| led[1] | 11 | LED 1 (ACC bit 1) |
| led[2] | 13 | LED 2 (ACC bit 2) |
| led[3] | 14 | LED 3 (ACC bit 3) |
| led[4] | 15 | LED 4 (ACC bit 4) |
| led[5] | 16 | LED 5 (ACC bit 5) |
| uart_tx | 17 | UART TX (debug, optional) |
| uart_rx | 18 | UART RX (debug, optional) |
| gpio[0]..gpio[5] | 27..32 | General-purpose PMOD pins during Gowin I2C bring-up |
| i2c_scl | 25 | PMOD pin reserved for Gowin I2C SCL |
| i2c_sda | 26 | PMOD pin reserved for Gowin I2C SDA |

## Loading Your Program

1. Edit `rom/program.mem` with your program (hex format)
2. Re-synthesize the design
3. Program the FPGA

Example program.mem:
```
@0
94    // LDI 20 -> RA=20
41    // MOV RD,RA
85    // LDI 5 -> RA=5
08    // ADD RA -> ACC=25
01    // HLT
```

## Clock Speed

Default CPU clock is 100 Hz (visible on LEDs). To change:

Edit `tang_nano_9k_top.sv`, line:
```verilog
localparam CLK_DIV = 135000;  // 100 Hz
```

Options:
- `CLK_DIV = 13500000` → 1 Hz (very slow, count LED blinks)
- `CLK_DIV = 135000` → 100 Hz (default, visible execution)
- `CLK_DIV = 1350` → 10 kHz (fast but not too fast)
- `CLK_DIV = 27` → 500 kHz (full speed)
- `CLK_DIV = 1` → 13.5 MHz (maximum speed)

## Synthesis Settings

In Gowin IDE:
1. Process → Configuration → Synthesize
2. Enable: "Verilog Language" = SystemVerilog 2012
3. Enable: "Infer RAM" for memory blocks

## Troubleshooting

### "Cannot find control_pkg"
Make sure `rtl/pkg/control_pkg.sv` is listed FIRST in the source files.

### "$readmemh file not found"
- Use relative path from project root
- Or use absolute path
- Or initialize memory in HDL code

### LEDs not changing
- Check CLK_DIV value (may be running too fast)
- Press S1 to reset
- Verify program.mem has correct syntax

## Resource Usage (Estimated)

| Resource | Used | Available | % |
|----------|------|-----------|---|
| LUT4 | ~800 | 8640 | 9% |
| FF | ~400 | 6480 | 6% |
| BSRAM | 2 | 26 | 8% |

The design easily fits on Tang Nano 9K with plenty of room for expansion.
