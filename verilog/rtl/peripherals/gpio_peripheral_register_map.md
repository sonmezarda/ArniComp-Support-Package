# GPIO Peripheral Register Map

This document describes the MMIO layout implemented by [gpio_peripheral.sv](/mnt/d/Projects/ArniComp-Support-Package/verilog/rtl/peripherals/gpio_peripheral.sv).

## Overview

- Base address: `0x0800`
- Address bus view inside the peripheral: `offset = mem_addr[7:0]`
- Data width: `8 bit`
- GPIO logical width:
  - `GPIO_WIDTH = 16` -> `GPIO0` covers bits `[7:0]`, `GPIO1` covers bits `[15:8]`
  - `GPIO_WIDTH = 8` -> only `GPIO0` is active, `GPIO1_*` registers read as `0x00` and writes are ignored
- PWM period width: `24 bit`
- PWM duty width: `12 bit`

## Port Naming

- `GPIO0` means GPIO bits `0..7`
- `GPIO1` means GPIO bits `8..15`
- Bit-alias registers use the full logical bit index `0..15`

## Behavior Summary

- `GPIO_IN` registers are read-only snapshots of synchronized pin inputs
- `GPIO_OUT` registers store the software-programmed output value
- `GPIO_DIR` registers control output enable
  - `0` = input / high-Z
  - `1` = output
- `GPIO_PWM_EN` registers select PWM output source per pin
  - `0` = normal digital output from `GPIO_OUT`
  - `1` = PWM waveform
- Physical pin drive is:
  - `gpio_oe = GPIO_DIR`
  - `gpio_out = GPIO_PWM_EN ? pwm_wave : GPIO_OUT`

## Real Registers

These are the main storage registers inside the peripheral.

| Absolute | Offset | Name | Access | Description |
|---|---:|---|---|---|
| `0x0800` | `0x00` | `GPIO0_IN` | `R` | Input bits `[7:0]` |
| `0x0801` | `0x01` | `GPIO1_IN` | `R` | Input bits `[15:8]` |
| `0x0802` | `0x02` | `GPIO0_OUT` | `R/W` | Output data bits `[7:0]` |
| `0x0803` | `0x03` | `GPIO1_OUT` | `R/W` | Output data bits `[15:8]` |
| `0x0804` | `0x04` | `GPIO0_DIR` | `R/W` | Direction bits `[7:0]` |
| `0x0805` | `0x05` | `GPIO1_DIR` | `R/W` | Direction bits `[15:8]` |
| `0x0806` | `0x06` | `GPIO0_PWM_EN` | `R/W` | PWM enable bits `[7:0]` |
| `0x0807` | `0x07` | `GPIO1_PWM_EN` | `R/W` | PWM enable bits `[15:8]` |
| `0x0808` | `0x08` | `GPIO0_PWM_PERIOD_LO` | `R/W` | GPIO0 PWM period bits `[7:0]` |
| `0x0809` | `0x09` | `GPIO0_PWM_PERIOD_MI` | `R/W` | GPIO0 PWM period bits `[15:8]` |
| `0x080A` | `0x0A` | `GPIO0_PWM_PERIOD_HI` | `R/W` | GPIO0 PWM period bits `[23:16]` |
| `0x080B` | `0x0B` | `GPIO1_PWM_PERIOD_LO` | `R/W` | GPIO1 PWM period bits `[7:0]` |
| `0x080C` | `0x0C` | `GPIO1_PWM_PERIOD_MI` | `R/W` | GPIO1 PWM period bits `[15:8]` |
| `0x080D` | `0x0D` | `GPIO1_PWM_PERIOD_HI` | `R/W` | GPIO1 PWM period bits `[23:16]` |

## Bit-Alias Registers

These are "fake registers": they do not add new storage. Each one reads or writes a single bit inside a real register.

Read value format:

- bit `0` = selected logical bit
- bits `[7:1]` = `0`

Write value format:

- bit `0` is used
- bits `[7:1]` are ignored

### Input Aliases

| Absolute Range | Offset Range | Meaning |
|---|---|---|
| `0x0810..0x081F` | `0x10..0x1F` | `GPIO_IN[0..15]` |

Examples:

- `0x0810` -> `GPIO_IN[0]`
- `0x0817` -> `GPIO_IN[7]`
- `0x0818` -> `GPIO_IN[8]`
- `0x081F` -> `GPIO_IN[15]`

### Output Aliases

| Absolute Range | Offset Range | Meaning |
|---|---|---|
| `0x0820..0x082F` | `0x20..0x2F` | `GPIO_OUT[0..15]` |

Examples:

- `0x0821` -> `GPIO_OUT[1]`
- Writing `0x01` sets that bit
- Writing `0x00` clears that bit

### Direction Aliases

| Absolute Range | Offset Range | Meaning |
|---|---|---|
| `0x0830..0x083F` | `0x30..0x3F` | `GPIO_DIR[0..15]` |

Examples:

- `0x0831` -> `GPIO_DIR[1]`
- Write `1` to make pin 1 an output
- Write `0` to make pin 1 an input

### PWM Enable Aliases

| Absolute Range | Offset Range | Meaning |
|---|---|---|
| `0x0840..0x084F` | `0x40..0x4F` | `GPIO_PWM_EN[0..15]` |

Examples:

- `0x0841` -> `GPIO_PWM_EN[1]`
- Write `1` to route PWM to pin 1
- Write `0` to route normal `GPIO_OUT` data

## PWM Duty Aliases

These are also "fake registers" over the internal per-pin duty storage.

Each pin uses two adjacent addresses:

- even address: duty low byte `[7:0]`
- odd address: duty high nibble `[11:8]` in bits `[3:0]`

Bits `[7:4]` of the HI address are read as `0` and ignored on write.

| Absolute Range | Offset Range | Meaning |
|---|---|---|
| `0x0850..0x086F` | `0x50..0x6F` | `GPIO_PWM_DUTY[0..15]`, interleaved LO/HI pairs |

Per-pin mapping:

| Pin | LO Address | HI Address |
|---:|---|---|
| 0 | `0x0850` | `0x0851` |
| 1 | `0x0852` | `0x0853` |
| 2 | `0x0854` | `0x0855` |
| 3 | `0x0856` | `0x0857` |
| 4 | `0x0858` | `0x0859` |
| 5 | `0x085A` | `0x085B` |
| 6 | `0x085C` | `0x085D` |
| 7 | `0x085E` | `0x085F` |
| 8 | `0x0860` | `0x0861` |
| 9 | `0x0862` | `0x0863` |
| 10 | `0x0864` | `0x0865` |
| 11 | `0x0866` | `0x0867` |
| 12 | `0x0868` | `0x0869` |
| 13 | `0x086A` | `0x086B` |
| 14 | `0x086C` | `0x086D` |
| 15 | `0x086E` | `0x086F` |

Example for pin 1:

- `0x0852` -> `GPIO_PWM_DUTY[1][7:0]`
- `0x0853` -> `GPIO_PWM_DUTY[1][11:8]`

Example 12-bit values:

- `0x000` -> 0%
- `0x800` -> about 50%
- `0xFFF` -> 100%

## PWM Frequency Formula

Each 8-bit GPIO port has one shared PWM period register:

- `GPIO0_PWM_PERIOD_*` controls pins `0..7`
- `GPIO1_PWM_PERIOD_*` controls pins `8..15`

Frequency:

```text
f_pwm = pwm_clk / (period + 1)
```

Examples with `pwm_clk = 27 MHz`:

- `period = 539 (0x00021B)` -> `50 kHz`
- `period = 26999 (0x006977)` -> `1 kHz`
- `period = 540000 - 1 = 539999 (0x083D5F)` -> about `50 Hz`

## PWM Duty Formula

Duty comparison is performed against the current period:

```text
high_count = duty / 4096 * (period + 1)
pwm_out = (counter < high_count)
```

Approximate examples:

- `duty = 0x000` -> 0%
- `duty = 0x400` -> 25%
- `duty = 0x800` -> 50%
- `duty = 0xC00` -> 75%
- `duty = 0xFFF` -> 100%

## Reset Values

On reset:

- `GPIO_OUT = 0x0000`
- `GPIO_DIR = 0x0000`
- `GPIO_PWM_EN = 0x0000`
- `GPIO_PWM_DUTY[x] = 0x000`
- `GPIO0_PWM_PERIOD = 540`
- `GPIO1_PWM_PERIOD = 540`

This means all pins start as inputs, with PWM disabled.

## 8-Bit Build Mode Notes

When `GPIO_WIDTH = 8`:

- only pins `0..7` are implemented physically
- `GPIO1_*` real registers are inactive
- bit aliases for pins `8..15` read as `0`
- writes targeting pins `8..15` are ignored

The address map does not change between 8-bit and 16-bit builds.
