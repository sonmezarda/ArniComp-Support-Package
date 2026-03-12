module flag_reg (
	clk,
	we,
	rst_n,
	lt_f_in,
	eq_f_in,
	gt_f_in,
	c_f_in,
	lt_f_out,
	eq_f_out,
	gt_f_out,
	c_f_out
);
	input wire clk;
	input wire we;
	input wire rst_n;
	input wire lt_f_in;
	input wire eq_f_in;
	input wire gt_f_in;
	input wire c_f_in;
	output wire lt_f_out;
	output wire eq_f_out;
	output wire gt_f_out;
	output wire c_f_out;
	reg_cell #(.W(4)) flag_register(
		.clk(clk),
		.rst_n(rst_n),
		.we(we),
		.oe(1'b1),
		.d({lt_f_in, eq_f_in, gt_f_in, c_f_in}),
		.out({lt_f_out, eq_f_out, gt_f_out, c_f_out})
	);
endmodule
