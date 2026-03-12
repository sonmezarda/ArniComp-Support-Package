module control_decoder (
	instr_in,
	ctrl_pkg_out,
	jmp_sel,
	reg_a_we,
	reg_b_we,
	reg_d_we,
	marl_we,
	marh_we,
	prl_we,
	prh_we,
	mem_we,
	acc_we
);
	reg _sv2v_0;
	input wire [7:0] instr_in;
	output wire [23:0] ctrl_pkg_out;
	output wire [2:0] jmp_sel;
	output reg reg_a_we;
	output reg reg_b_we;
	output reg reg_d_we;
	output reg marl_we;
	output reg marh_we;
	output reg prl_we;
	output reg prh_we;
	output reg mem_we;
	output wire acc_we;
	control_rom control_rom_i(
		.instr(instr_in),
		.ctrl(ctrl_pkg_out)
	);
	assign jmp_sel = instr_in[2:0];
	assign acc_we = ctrl_pkg_out[13];
	always @(*) begin
		if (_sv2v_0)
			;
		reg_a_we = 1'b0;
		reg_d_we = 1'b0;
		reg_b_we = 1'b0;
		marl_we = 1'b0;
		marh_we = 1'b0;
		prl_we = 1'b0;
		prh_we = 1'b0;
		mem_we = 1'b0;
		if (ctrl_pkg_out[14])
			case (ctrl_pkg_out[12-:3])
				3'b000: reg_a_we = 1'b1;
				3'b001: reg_d_we = 1'b1;
				3'b010: reg_b_we = 1'b1;
				3'b011: marl_we = 1'b1;
				3'b100: marh_we = 1'b1;
				3'b101: prl_we = 1'b1;
				3'b110: prh_we = 1'b1;
				3'b111: mem_we = 1'b1;
			endcase
	end
	initial _sv2v_0 = 0;
endmodule
