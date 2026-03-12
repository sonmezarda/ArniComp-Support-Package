module program_counter (
	clk,
	rst_n,
	count_en,
	load_en,
	load_data,
	paddr
);
	reg _sv2v_0;
	input wire clk;
	input wire rst_n;
	input wire count_en;
	input wire load_en;
	input wire [15:0] load_data;
	output wire [15:0] paddr;
	wire [15:0] pc_q;
	reg [15:0] pc_next;
	always @(*) begin
		if (_sv2v_0)
			;
		pc_next = pc_q;
		if (load_en)
			pc_next = load_data;
		else if (count_en)
			pc_next = pc_next + 16'd1;
	end
	reg_cell #(
		.W(16),
		.RESET_VALUE(16'h0000)
	) program_reg(
		.clk(clk),
		.rst_n(rst_n),
		.we(load_en | count_en),
		.oe(1'b1),
		.d(pc_next),
		.out(pc_q)
	);
	assign paddr = pc_q;
	initial _sv2v_0 = 0;
endmodule
