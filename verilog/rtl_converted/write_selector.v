module write_selector (
	write_sel,
	a,
	d,
	b,
	marl,
	marh,
	prl,
	prh,
	m
);
	reg _sv2v_0;
	input wire [2:0] write_sel;
	output reg a;
	output reg d;
	output reg b;
	output reg marl;
	output reg marh;
	output reg prl;
	output reg prh;
	output reg m;
	always @(*) begin
		if (_sv2v_0)
			;
		a = 1'b0;
		d = 1'b0;
		b = 1'b0;
		marl = 1'b0;
		marh = 1'b0;
		prl = 1'b0;
		prh = 1'b0;
		m = 1'b0;
		case (write_sel)
			3'b000: a = 1'b1;
			3'b001: d = 1'b1;
			3'b010: b = 1'b1;
			3'b011: marl = 1'b1;
			3'b100: marh = 1'b1;
			3'b101: prl = 1'b1;
			3'b110: prh = 1'b1;
			3'b111: m = 1'b1;
			default:
				;
		endcase
	end
	initial _sv2v_0 = 0;
endmodule
