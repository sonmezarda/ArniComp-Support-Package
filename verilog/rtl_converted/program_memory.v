module program_memory (
	clk,
	addr,
	data
);
	parameter signed [31:0] ADDR_WIDTH = 16;
	parameter signed [31:0] DATA_WIDTH = 8;
	parameter signed [31:0] MEM_SIZE = 256;
	parameter MEM_FILE = "../rom/program.mem";
	input wire clk;
	input wire [ADDR_WIDTH - 1:0] addr;
	output reg [DATA_WIDTH - 1:0] data;
	reg [DATA_WIDTH - 1:0] mem [0:MEM_SIZE - 1];
	initial if (MEM_FILE != "")
		$readmemh(MEM_FILE, mem);
	always @(posedge clk) data <= mem[addr[7:0]];
endmodule
