module data_memory (
	clk,
	we,
	addr,
	data_in,
	data_out
);
	parameter signed [31:0] ADDR_WIDTH = 16;
	parameter signed [31:0] DATA_WIDTH = 8;
	parameter signed [31:0] MEM_SIZE = 256;
	input wire clk;
	input wire we;
	input wire [ADDR_WIDTH - 1:0] addr;
	input wire [DATA_WIDTH - 1:0] data_in;
	output wire [DATA_WIDTH - 1:0] data_out;
	reg [DATA_WIDTH - 1:0] mem [0:MEM_SIZE - 1];
	wire [7:0] mem_addr = addr[7:0];
	always @(posedge clk)
		if (we)
			mem[mem_addr] <= data_in;
	assign data_out = mem[mem_addr];
endmodule
