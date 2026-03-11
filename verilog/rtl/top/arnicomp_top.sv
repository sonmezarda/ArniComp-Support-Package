module arnicomp_top #(
    parameter string PROG_MEM_FILE = ""
)(
    input logic       clk,
    input logic       rst_n
);

import control_pkg::*;

logic jump_taken;
logic [2:0] jmp_select;

logic [7:0] inst_q;

logic less_flag;
logic equal_flag;
logic greater_flag;
logic carry_flag;

logic lf_reg_out;
logic eq_reg_out;
logic gt_reg_out;
logic c_reg_out;

logic [7:0] alu_out;
logic [7:0] reg_a_out;
logic [7:0] reg_b_out;
logic [7:0] reg_d_out;
logic [7:0] acc_out;
logic [7:0] marl_out;
logic [7:0] marh_out;
logic [7:0] prl_out;
logic [7:0] prh_out;
logic [15:0] pc_addr;

logic reg_a_we;
logic reg_b_we;
logic reg_d_we;
logic acc_we;
logic marl_we;
logic marh_we;
logic prl_we;
logic prh_we;
logic mem_we;

logic [7:0] bus;
logic [7:0] mem_data_out;
logic [15:0] mar_addr;
assign mar_addr = {marh_out, marl_out};

control_pkg::ctrl_t control_pins;

// Memory Subsystem

program_memory #(
    .MEM_FILE(PROG_MEM_FILE)
) prog_mem (
    .clk(clk),
    .addr(pc_addr),
    .data(inst_q)
);

data_memory data_mem (
    .clk(clk),
    .we(mem_we),
    .addr(mar_addr),
    .data_in(bus),
    .data_out(mem_data_out)
);

// Bus Selector 

logic [7:0] bus_sel_out;

bus_selector bus_selector_i(
    .sel(control_pins.ssel),
    .a(reg_a_out),
    .d(reg_d_out),
    .b(reg_b_out),
    .acc(acc_out),
    .pcl(pc_addr[7:0]),
    .pch(pc_addr[15:8]),
    .m(mem_data_out),
    .out(bus_sel_out)
);

// Im7: Use 7-bit immediate from instruction byte
// Im3: Use 3-bit immediate from instruction byte 
assign bus = control_pins.im7 ? {1'b0, inst_q[6:0]} :
             control_pins.im3 ? {{5{1'b0}}, inst_q[2:0]} :
             bus_sel_out;

reg_a reg_a_i(
    .clk(clk),
    .rst_n(rst_n),
    .we(reg_a_we),
    .smsbra(control_pins.smsbra),
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
    .inc(control_pins.inc),
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

logic [15:0] jump_addr;
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
    .we(control_pins.sf),
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
    .count_en(control_pins.ce),
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

logic alu_carry_out;

// ALU carry input
logic alu_carry_in;
assign alu_carry_in = control_pins.sc ? c_reg_out : control_pins.sn;

alu alu_i(
    .a(reg_d_out),     // RD is always the first operand
    .b(bus),           // Source register or immediate (from bus)
    .ops(control_pins.ops),
    .negative(control_pins.sn),
    .c_in(alu_carry_in),
    .result(alu_out),
    .carry_flag(alu_carry_out)
);

assign carry_flag = alu_carry_out;

jump_logic jump_decoder(
    .jmp_en(control_pins.jmp),
    .carry_flag(c_reg_out),
    .equal_flag(eq_reg_out),
    .greater_flag(gt_reg_out),
    .less_flag(lf_reg_out),
    .jmp_cond(jmp_select),
    .jmp_taken(jump_taken)
);

endmodule