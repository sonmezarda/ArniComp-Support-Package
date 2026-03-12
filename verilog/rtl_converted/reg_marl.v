module reg_marl (
	clk,
	rst_n,
	we,
	inc,
	d,
	out
);
	reg _sv2v_0;
	input wire clk;
	input wire rst_n;
	input wire we;
	input wire inc;
	input wire [7:0] d;
	output wire [7:0] out;
	reg [7:0] data_in;
	always @(*) begin
		if (_sv2v_0)
			;
		if (inc)
			data_in = out + 8'd1;
		else
			data_in = d;
	end
	reg_cell #(
		.W(8),
		.RESET_VALUE(8'h00)
	) marl_cell(
		.clk(clk),
		.rst_n(rst_n),
		.we(we | inc),
		.oe(1'b1),
		.d(data_in),
		.out(out)
	);
	initial _sv2v_0 = 0;
endmodule
