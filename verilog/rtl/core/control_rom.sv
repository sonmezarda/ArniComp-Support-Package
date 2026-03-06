`timescale 1ns/1ps
module control_rom #(
    parameter string ROM_FILE = "control_rom.hex"
)(
    input  logic [7:0] instr,
    output control_pkg::ctrl_t ctrl
);

    import control_pkg::*;

    logic [7:0] rom0 [0:255];
    logic [7:0] rom1 [0:255];
    logic [7:0] rom2 [0:255];

    initial begin
        $display("Loading control ROM...");
        $readmemh("rom/rom0.mem", rom0);
        $readmemh("rom/rom1.mem", rom1);
        $readmemh("rom/rom2.mem", rom2);
    end

    logic [CTRL_W-1:0] ctrl_raw;

    assign ctrl_raw = {rom2[instr], rom1[instr], rom0[instr]};
    assign ctrl = ctrl_t'(ctrl_raw);

endmodule