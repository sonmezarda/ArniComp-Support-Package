module bus_selector (
	sel,
	a,
	d,
	b,
	acc,
	pcl,
	pch,
	m,
	out
);
	reg _sv2v_0;
	input wire [2:0] sel;
	input wire [7:0] a;
	input wire [7:0] d;
	input wire [7:0] b;
	input wire [7:0] acc;
	input wire [7:0] pcl;
	input wire [7:0] pch;
	input wire [7:0] m;
	output wire [7:0] out;
	reg [7:0] out_sel;
	always @(*) begin
		if (_sv2v_0)
			;
		case (sel)
			3'b000: out_sel = a;
			3'b001: out_sel = d;
			3'b010: out_sel = b;
			3'b011: out_sel = acc;
			3'b100: out_sel = pcl;
			3'b101: out_sel = pch;
			3'b110: out_sel = 8'h00;
			3'b111: out_sel = m;
			default: out_sel = 8'h00;
		endcase
	end
	assign out = out_sel;
	initial _sv2v_0 = 0;
endmodule
