module arnicomp_top (
	clk,
	rst_n
);
	parameter PROG_MEM_FILE = "";
	input wire clk;
	input wire rst_n;
	wire jump_taken;
	wire [2:0] jmp_select;
	wire [7:0] inst_q;
	wire less_flag;
	wire equal_flag;
	wire greater_flag;
	wire carry_flag;
	wire lf_reg_out;
	wire eq_reg_out;
	wire gt_reg_out;
	wire c_reg_out;
	wire [7:0] alu_out;
	wire [7:0] reg_a_out;
	wire [7:0] reg_b_out;
	wire [7:0] reg_d_out;
	wire [7:0] acc_out;
	wire [7:0] marl_out;
	wire [7:0] marh_out;
	wire [7:0] prl_out;
	wire [7:0] prh_out;
	wire [15:0] pc_addr;
	wire reg_a_we;
	wire reg_b_we;
	wire reg_d_we;
	wire acc_we;
	wire marl_we;
	wire marh_we;
	wire prl_we;
	wire prh_we;
	wire mem_we;
	wire [7:0] bus;
	wire [7:0] mem_data_out;
	wire [15:0] mar_addr;
	assign mar_addr = {marh_out, marl_out};
	wire [23:0] control_pins;
	program_memory #(.MEM_FILE(PROG_MEM_FILE)) prog_mem(
		.clk(clk),
		.addr(pc_addr),
		.data(inst_q)
	);
	data_memory data_mem(
		.clk(clk),
		.we(mem_we),
		.addr(mar_addr),
		.data_in(bus),
		.data_out(mem_data_out)
	);
	wire [7:0] bus_sel_out;
	bus_selector bus_selector_i(
		.sel(control_pins[4-:3]),
		.a(reg_a_out),
		.d(reg_d_out),
		.b(reg_b_out),
		.acc(acc_out),
		.pcl(pc_addr[7:0]),
		.pch(pc_addr[15:8]),
		.m(mem_data_out),
		.out(bus_sel_out)
	);
	assign bus = (control_pins[0] ? {1'b0, inst_q[6:0]} : (control_pins[8] ? {{5 {1'b0}}, inst_q[2:0]} : bus_sel_out));
	reg_a reg_a_i(
		.clk(clk),
		.rst_n(rst_n),
		.we(reg_a_we),
		.smsbra(control_pins[5]),
		.d(bus),
		.out(reg_a_out)
	);
	reg_cell #(.W(8)) reg_b(
		.clk(clk),
		.rst_n(rst_n),
		.we(reg_b_we),
		.oe(1'b1),
		.d(bus),
		.out(reg_b_out)
	);
	reg_cell #(.W(8)) reg_d(
		.clk(clk),
		.rst_n(rst_n),
		.we(reg_d_we),
		.oe(1'b1),
		.d(bus),
		.out(reg_d_out)
	);
	reg_cell #(.W(8)) acc(
		.clk(clk),
		.rst_n(rst_n),
		.we(acc_we),
		.oe(1'b1),
		.d(alu_out),
		.out(acc_out)
	);
	reg_marl marl_i(
		.clk(clk),
		.rst_n(rst_n),
		.we(marl_we),
		.inc(control_pins[22]),
		.d(bus),
		.out(marl_out)
	);
	reg_cell #(.W(8)) marh(
		.clk(clk),
		.rst_n(rst_n),
		.we(marh_we),
		.oe(1'b1),
		.d(bus),
		.out(marh_out)
	);
	reg_cell #(.W(8)) prl(
		.clk(clk),
		.rst_n(rst_n),
		.we(prl_we),
		.oe(1'b1),
		.d(bus),
		.out(prl_out)
	);
	reg_cell #(.W(8)) prh(
		.clk(clk),
		.rst_n(rst_n),
		.we(prh_we),
		.oe(1'b1),
		.d(bus),
		.out(prh_out)
	);
	wire [15:0] jump_addr;
	assign jump_addr = {prh_out, prl_out};
	comparator comparator(
		.a(reg_d_out),
		.b(bus),
		.less_flag(less_flag),
		.equal_flag(equal_flag),
		.greater_flag(greater_flag)
	);
	flag_reg flag_reg_i(
		.clk(clk),
		.we(control_pins[9]),
		.rst_n(rst_n),
		.lt_f_in(less_flag),
		.eq_f_in(equal_flag),
		.gt_f_in(greater_flag),
		.c_f_in(carry_flag),
		.lt_f_out(lf_reg_out),
		.eq_f_out(eq_reg_out),
		.gt_f_out(gt_reg_out),
		.c_f_out(c_reg_out)
	);
	program_counter pc(
		.clk(clk),
		.rst_n(rst_n),
		.count_en(control_pins[18]),
		.load_en(jump_taken),
		.load_data(jump_addr),
		.paddr(pc_addr)
	);
	control_decoder instruction_decoder(
		.instr_in(inst_q),
		.ctrl_pkg_out(control_pins),
		.jmp_sel(jmp_select),
		.reg_a_we(reg_a_we),
		.reg_b_we(reg_b_we),
		.reg_d_we(reg_d_we),
		.marl_we(marl_we),
		.marh_we(marh_we),
		.prl_we(prl_we),
		.prh_we(prh_we),
		.mem_we(mem_we),
		.acc_we(acc_we)
	);
	wire alu_carry_out;
	wire alu_carry_in;
	assign alu_carry_in = (control_pins[16] ? c_reg_out : control_pins[19]);
	alu alu_i(
		.a(reg_d_out),
		.b(bus),
		.ops(control_pins[21-:2]),
		.negative(control_pins[19]),
		.c_in(alu_carry_in),
		.result(alu_out),
		.carry_flag(alu_carry_out)
	);
	assign carry_flag = alu_carry_out;
	jump_logic jump_decoder(
		.jmp_en(control_pins[17]),
		.carry_flag(c_reg_out),
		.equal_flag(eq_reg_out),
		.greater_flag(gt_reg_out),
		.less_flag(lf_reg_out),
		.jmp_cond(jmp_select),
		.jmp_taken(jump_taken)
	);
endmodule
