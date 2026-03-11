`timescale 1ns/1ps

module program_memory #(
    parameter int ADDR_WIDTH = 16,
    parameter int DATA_WIDTH = 8,
    parameter int MEM_SIZE   = 65536,
    parameter string MEM_FILE = ""
)(
    input  logic                    clk,
    input  logic [ADDR_WIDTH-1:0]   addr,
    output logic [DATA_WIDTH-1:0]   data
);

    logic [DATA_WIDTH-1:0] mem [0:MEM_SIZE-1];

    initial begin
        // Initialize memory to NOP (0x00)
        for (int i = 0; i < MEM_SIZE; i++) begin
            mem[i] = 8'h00;
        end
        
        // Load program if file specified
        if (MEM_FILE != "") begin
            $display("Loading program memory from %s", MEM_FILE);
            $readmemh(MEM_FILE, mem);
        end
    end

    // Synchronous read
    always_ff @(posedge clk) begin
        data <= mem[addr];
    end

endmodule
