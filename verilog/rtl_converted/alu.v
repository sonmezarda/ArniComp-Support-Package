module alu (
	a,
	b,
	ops,
	negative,
	c_in,
	result,
	carry_flag
);
	reg _sv2v_0;
	input wire [7:0] a;
	input wire [7:0] b;
	input wire [1:0] ops;
	input wire negative;
	input wire c_in;
	output wire [7:0] result;
	output wire carry_flag;
	reg [7:0] sum;
	reg carry_out;
	reg [8:0] arith_tmp;
	always @(*) begin
		if (_sv2v_0)
			;
		sum = 1'sb0;
		carry_out = 1'b0;
		arith_tmp = 1'sb0;
		case (ops)
			2'b00:
				if (!negative) begin
					arith_tmp = ({1'b0, a} + {1'b0, b}) + {8'b00000000, c_in};
					carry_out = arith_tmp[8];
					sum = arith_tmp[7:0];
				end
				else begin
					arith_tmp = ({1'b0, a} - {1'b0, b}) - {8'b00000000, ~c_in};
					carry_out = ~arith_tmp[8];
					sum = arith_tmp[7:0];
				end
			2'b01: sum = a & b;
			2'b10: sum = a ^ b;
			2'b11: sum = ~b;
		endcase
	end
	assign result = sum;
	assign carry_flag = carry_out;
	initial _sv2v_0 = 0;
endmodule
