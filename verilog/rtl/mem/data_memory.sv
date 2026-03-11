`timescale 1ns/1ps

module data_memory #(
    parameter int ADDR_WIDTH = 16,
    parameter int DATA_WIDTH = 8,
    parameter int MEM_SIZE   = 65536
)(
    input  logic                    clk,
    input  logic                    we,
    input  logic [ADDR_WIDTH-1:0]   addr,
    input  logic [DATA_WIDTH-1:0]   data_in,
    output logic [DATA_WIDTH-1:0]   data_out
);

    logic [DATA_WIDTH-1:0] mem [0:MEM_SIZE-1];

    initial begin
        // Initialize memory to zero
        for (int i = 0; i < MEM_SIZE; i++) begin
            mem[i] = 8'h00;
        end
    end

    // Synchronous write, asynchronous read
    always_ff @(posedge clk) begin
        if (we) begin
            mem[addr] <= data_in;
        end
    end

    // Asynchronous read for combinational bus access
    assign data_out = mem[addr];

endmodule
