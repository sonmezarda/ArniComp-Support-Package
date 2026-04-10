# I2C Peripheral Register Map

This document describes the MMIO layout implemented by [i2c_peripheral.sv](/mnt/d/Projects/ArniComp-Support-Package/verilog/rtl/peripherals/i2c_peripheral.sv).

## Overview

- Base address: `0x0A00`
- Address bus view inside the peripheral: `offset = mem_addr[7:0]`
- Data width: `8 bit`
- Backend IP: Gowin `I2C_MASTER_Top`
- Bus model: CPU writes command/data registers, then polls status until transfer completion

## Register Summary

| Absolute | Offset | Name | Access | Description |
|---|---:|---|---|---|
| `0x0A00` | `0x00` | `PRESCALE_LO` | `R/W` | Clock prescale low byte |
| `0x0A01` | `0x01` | `PRESCALE_HI` | `R/W` | Clock prescale high byte |
| `0x0A02` | `0x02` | `CONTROL` | `R/W` | Gowin control register |
| `0x0A03` | `0x03` | `TXR_RXR` | `W/R` | Write transmit byte, read back the last queued TX byte |
| `0x0A04` | `0x04` | `CR_SR` | `W/R` | Write command byte, read cached status byte |
| `0x0A05` | `0x05` | `INT` | `R` | Raw `O_IIC_INT` level in bit `0` |

## Gowin Register Behavior

- `PRESCALE_LO` and `PRESCALE_HI` form a 16-bit divider:
  - `prescale = (input_clk / (5 * scl_freq)) - 1`
- `CONTROL`:
  - bit `7` = `EN`
  - bit `6` = `IEN`
- `TXR_RXR`:
  - write: transmit register
  - read: receive register snapshot
- `CR_SR`:
  - write: command register
  - read: status register snapshot

## Command Register (`0x0A04` write)

- bit `7` = `STA`
- bit `6` = `STO`
- bit `5` = `RD`
- bit `4` = `WR`
- bit `3` = `ACK`
- bit `0` = `IACK`

Common values:

- `0x90` = `STA | WR`
- `0x10` = `WR`
- `0x20` = `RD`
- `0x50` = `STO | WR`
- `0x68` = `STO | RD | ACK`

## Status Register (`0x0A04` read)

- bit `7` = `RX_ACK`
  - `1` = no ACK received
  - `0` = ACK received
- bit `6` = `BUSY`
- bit `5` = `AL`
- bit `1` = `TIP`
- bit `0` = `IF`

## Wrapper Notes

- The Gowin IP uses a synchronous SRAM-style read interface.
- The wrapper keeps CPU-visible shadow registers and runs a small internal sequencer for command writes.
- Writing `0x04` launches a hardware-side `TXR -> CR -> status poll` sequence so the CPU can keep using the existing single-cycle MMIO model.
- The live Gowin status register is polled internally and the latest cached snapshot is exposed at `0x04`.
- `0x03` currently reads back the last byte written to `TXR`.
- This keeps CPU-side MMIO access aligned with the existing single-byte peripheral style used by GPIO and UART while avoiding direct asynchronous reads from the vendor core's synchronous SRAM-style interface.
- The status snapshot may still lag the live IP state by a small number of `cpu_clk` cycles, but command completion is now tracked by the wrapper instead of depending on ad-hoc read timing.

## Bring-Up Sequence

1. Program `PRESCALE_LO` and `PRESCALE_HI`
2. Write `0x80` to `CONTROL` to enable the master
3. Write slave address plus R/W bit to `TXR_RXR`
4. Write command byte to `CR_SR`
5. Poll `CR_SR` until `TIP` becomes `0`
6. Check `RX_ACK` and continue with the next byte or stop command
