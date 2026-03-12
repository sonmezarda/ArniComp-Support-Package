module control_rom (
	instr,
	ctrl
);
	parameter ROM_FILE = "../rom/control_rom.mem";
	input wire [7:0] instr;
	output wire [23:0] ctrl;
	localparam signed [31:0] control_pkg_CTRL_W = 24;
	reg [23:0] rom [0:255];
	initial begin
		$display("Loading control ROM from %s", ROM_FILE);
		$readmemh(ROM_FILE, rom);
	end
	function automatic [23:0] sv2v_cast_24;
		input reg [23:0] inp;
		sv2v_cast_24 = inp;
	endfunction
	assign ctrl = sv2v_cast_24(rom[instr]);
endmodule
