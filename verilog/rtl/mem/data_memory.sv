`timescale 1ns/1ps

module data_memory #(
    parameter int ADDR_WIDTH = 16,
    parameter int DATA_WIDTH = 8,
    parameter int MEM_SIZE   = 256  // Small for FPGA demo
)(
    input  logic                    clk,
    input  logic                    we,
    input  logic [ADDR_WIDTH-1:0]   addr,
    input  logic [DATA_WIDTH-1:0]   data_in,
    output logic [DATA_WIDTH-1:0]   data_out
);
    logic [DATA_WIDTH-1:0] mem [0:MEM_SIZE-1];
    
    wire [7:0] mem_addr = addr[7:0];

    // Synchronous write
    always_ff @(posedge clk) begin
        if (we) begin
            mem[mem_addr] <= data_in;
        end
    end

    // Asynchronous read (required for single-cycle bus access)
    assign data_out = mem[mem_addr];

endmodule
