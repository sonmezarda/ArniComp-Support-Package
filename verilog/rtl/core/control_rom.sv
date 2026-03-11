`timescale 1ns/1ps
module control_rom #(
    parameter string ROM_FILE = "rom/control_rom.mem"
)(
    input  logic [7:0] instr,
    output control_pkg::ctrl_t ctrl
);

    import control_pkg::*;

    // Single 24-bit ROM (256 entries)
    logic [CTRL_W-1:0] rom [0:255];

    initial begin
        $display("Loading control ROM from %s", ROM_FILE);
        $readmemh(ROM_FILE, rom);
    end

    assign ctrl = ctrl_t'(rom[instr]);

endmodule