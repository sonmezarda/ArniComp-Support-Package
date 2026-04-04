`timescale 1ns/1ps

module program_memory #(
    parameter int ADDR_WIDTH = 16,
    parameter int DATA_WIDTH = 8,
    parameter int MEM_SIZE   = 512,
    parameter string MEM_FILE = ""
)(
    input  logic                    clk,
    input  logic [ADDR_WIDTH-1:0]   addr,
    output logic [DATA_WIDTH-1:0]   data
);

    localparam int MEM_ADDR_WIDTH = (MEM_SIZE <= 2) ? 1 : $clog2(MEM_SIZE);

    logic [DATA_WIDTH-1:0] mem [0:MEM_SIZE-1];
    wire [MEM_ADDR_WIDTH-1:0] mem_addr = addr[MEM_ADDR_WIDTH-1:0];

    // Program memory contents are loaded from a hex file at synthesis/simulation time.
    logic [DATA_WIDTH-1:0] mem [0:MEM_SIZE-1];

    initial begin
        if (MEM_FILE != "") begin
            $readmemh(MEM_FILE, mem);
        end
    end

    // Synchronous read is the pattern Gowin is most likely to infer as block ROM.
    always_ff @(posedge clk) begin
        data <= mem[mem_addr];
    end

endmodule
