#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT_DIR/visualization"
SV2V_BIN="$ROOT_DIR/sv2v-Linux/sv2v"
CONVERTED_V="$OUT_DIR/arnicomp_soc_top_converted.v"

mkdir -p "$OUT_DIR"

"$SV2V_BIN" \
  "$ROOT_DIR/rtl/pkg/control_pkg.sv" \
  "$ROOT_DIR/rtl/blocks/alu.sv" \
  "$ROOT_DIR/rtl/blocks/comparator.sv" \
  "$ROOT_DIR/rtl/blocks/program_counter.sv" \
  "$ROOT_DIR/rtl/core/bus_selector.sv" \
  "$ROOT_DIR/rtl/core/control_decoder.sv" \
  "$ROOT_DIR/rtl/core/control_rom.sv" \
  "$ROOT_DIR/rtl/core/flag_reg.sv" \
  "$ROOT_DIR/rtl/core/jump_logic.sv" \
  "$ROOT_DIR/rtl/core/reg_a.sv" \
  "$ROOT_DIR/rtl/core/reg_marl.sv" \
  "$ROOT_DIR/rtl/lib/reg_cell.sv" \
  "$ROOT_DIR/rtl/lib/async_fifo.sv" \
  "$ROOT_DIR/rtl/mem/data_memory.sv" \
  "$ROOT_DIR/rtl/mem/memory_map_unit.sv" \
  "$ROOT_DIR/rtl/mem/program_memory.sv" \
  "$ROOT_DIR/rtl/peripherals/uart_peripheral.sv" \
  "$ROOT_DIR/rtl/top/arnicomp_top.sv" \
  "$ROOT_DIR/rtl/top/arnicomp_soc_top.sv" \
  "$ROOT_DIR/rtl/vendor/uart_module/rtl/sync_fifo.sv" \
  "$ROOT_DIR/rtl/vendor/uart_module/rtl/uart_baud_rate.sv" \
  "$ROOT_DIR/rtl/vendor/uart_module/rtl/uart_rx.sv" \
  "$ROOT_DIR/rtl/vendor/uart_module/rtl/uart_top.sv" \
  "$ROOT_DIR/rtl/vendor/uart_module/rtl/uart_tx.sv" \
  --top=arnicomp_soc_top \
  --write="$CONVERTED_V"

yosys -p "read_verilog $CONVERTED_V; hierarchy -top arnicomp_soc_top; proc; show -format svg -prefix $OUT_DIR/arnicomp_soc_top_blocks -stretch arnicomp_soc_top"
yosys -p "read_verilog $CONVERTED_V; hierarchy -top arnicomp_soc_top; proc; opt; show -format svg -prefix $OUT_DIR/arnicomp_soc_top_detailed -stretch arnicomp_soc_top"
yosys -p "read_verilog $CONVERTED_V; hierarchy -top arnicomp_top; proc; show -format svg -prefix $OUT_DIR/arnicomp_cpu_block -stretch arnicomp_top"
yosys -p "read_verilog $CONVERTED_V; hierarchy -top uart_peripheral; proc; show -format svg -prefix $OUT_DIR/uart_peripheral_block -stretch uart_peripheral"

yosys -p "read_verilog $CONVERTED_V; prep -top arnicomp_soc_top; write_json $OUT_DIR/arnicomp_soc_top_netlist.json"
netlistsvg "$OUT_DIR/arnicomp_soc_top_netlist.json" -o "$OUT_DIR/arnicomp_soc_top_netlistsvg.svg"

yosys -p "read_verilog $CONVERTED_V; prep -top arnicomp_soc_top -flatten; write_json $OUT_DIR/arnicomp_soc_top_flat_netlist.json"
netlistsvg "$OUT_DIR/arnicomp_soc_top_flat_netlist.json" -o "$OUT_DIR/arnicomp_soc_top_flat_netlistsvg.svg"

yosys -p "read_verilog $CONVERTED_V; prep -top arnicomp_top; write_json $OUT_DIR/arnicomp_cpu_netlist.json"
netlistsvg "$OUT_DIR/arnicomp_cpu_netlist.json" -o "$OUT_DIR/arnicomp_cpu_netlistsvg.svg"

yosys -p "read_verilog $CONVERTED_V; prep -top uart_peripheral; write_json $OUT_DIR/uart_peripheral_netlist.json"
netlistsvg "$OUT_DIR/uart_peripheral_netlist.json" -o "$OUT_DIR/uart_peripheral_netlistsvg.svg"

printf 'Generated SVG files in %s\n' "$OUT_DIR"
