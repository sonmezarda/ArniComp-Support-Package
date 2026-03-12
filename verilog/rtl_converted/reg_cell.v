module reg_cell (
	clk,
	rst_n,
	we,
	oe,
	d,
	out
);
	parameter signed [31:0] W = 8;
	parameter [W - 1:0] RESET_VALUE = 1'sb0;
	input wire clk;
	input wire rst_n;
	input wire we;
	input wire oe;
	input wire [W - 1:0] d;
	output wire [W - 1:0] out;
	reg [W - 1:0] reg_q;
	always @(posedge clk or negedge rst_n)
		if (~rst_n)
			reg_q <= RESET_VALUE;
		else if (we)
			reg_q <= d;
	assign out = (oe ? reg_q : {W {1'sb0}});
endmodule
