module jump_logic (
	jmp_en,
	carry_flag,
	equal_flag,
	greater_flag,
	less_flag,
	jmp_cond,
	jmp_taken
);
	reg _sv2v_0;
	input wire jmp_en;
	input wire carry_flag;
	input wire equal_flag;
	input wire greater_flag;
	input wire less_flag;
	input wire [2:0] jmp_cond;
	output reg jmp_taken;
	always @(*) begin
		if (_sv2v_0)
			;
		jmp_taken = 1'b0;
		if (jmp_en)
			case (jmp_cond)
				3'b000: jmp_taken = 1'b1;
				3'b001: jmp_taken = equal_flag;
				3'b010: jmp_taken = greater_flag;
				3'b011: jmp_taken = less_flag;
				3'b100: jmp_taken = greater_flag | equal_flag;
				3'b101: jmp_taken = less_flag | equal_flag;
				3'b110: jmp_taken = ~equal_flag;
				3'b111: jmp_taken = carry_flag;
				default: jmp_taken = 1'b0;
			endcase
	end
	initial _sv2v_0 = 0;
endmodule
