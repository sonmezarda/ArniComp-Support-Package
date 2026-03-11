`timescale 1ns/1ps

module program_memory #(
    parameter int ADDR_WIDTH = 16,
    parameter int DATA_WIDTH = 8,
    parameter int MEM_SIZE   = 256,  // Small for FPGA demo
    parameter string MEM_FILE = ""
)(
    input  logic                    clk,
    input  logic [ADDR_WIDTH-1:0]   addr,
    output logic [DATA_WIDTH-1:0]   data
);

    // 256 bytes program memory - fits in BSRAM
    logic [DATA_WIDTH-1:0] mem [0:MEM_SIZE-1];

    initial begin
        if (MEM_FILE != "") begin
            $readmemh(MEM_FILE, mem);
        end
    end

    // Synchronous read for BSRAM inference
    always_ff @(posedge clk) begin
        data <= mem[addr[7:0]];
    end

endmodule
