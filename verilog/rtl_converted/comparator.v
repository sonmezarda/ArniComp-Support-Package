module comparator (
	a,
	b,
	less_flag,
	equal_flag,
	greater_flag
);
	reg _sv2v_0;
	input wire [7:0] a;
	input wire [7:0] b;
	output reg less_flag;
	output reg equal_flag;
	output reg greater_flag;
	always @(*) begin
		if (_sv2v_0)
			;
		less_flag = a < b;
		equal_flag = a == b;
		greater_flag = a > b;
	end
	initial _sv2v_0 = 0;
endmodule
