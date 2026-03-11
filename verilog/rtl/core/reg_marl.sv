`timescale 1ns/1ps

// MARL Register with INX (increment) support
// INX instruction increments MARL by 1
module reg_marl (
    input  logic       clk,
    input  logic       rst_n,
    input  logic       we,
    input  logic       inc,
    input  logic [7:0] d,
    output logic [7:0] out
);

    logic [7:0] data_in;
    
    always_comb begin
        if (inc)
            data_in = out + 8'd1;  // Increment
        else
            data_in = d;
    end

    reg_cell #(
        .W(8),
        .RESET_VALUE(8'h00)
    ) marl_cell (
        .clk(clk),
        .rst_n(rst_n),
        .we(we | inc),
        .oe(1'b1),
        .d(data_in),
        .out(out)
    );

endmodule
