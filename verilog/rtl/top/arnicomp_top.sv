module arnicomp_top #(
    parameter string PROG_MEM_FILE = ""
)(
    input logic       clk,
    input logic       rst_n
);

import control_pkg::*;

logic jump_taken = 1'b0;
logic [2:0] jmp_select = 3'b000;

logic [7:0] inst_q;

logic less_flag    = 1'b0;
logic equal_flag   = 1'b0;
logic greater_flag = 1'b0;
logic carry_flag   = 1'b0;

logic lf_reg_out;
logic eq_reg_out;
logic gt_reg_out;
logic c_reg_out;

logic [7:0] alu_out   = '0;
logic [7:0] reg_a_out = '0;
logic [7:0] reg_b_out = '0;
logic [7:0] reg_d_out = '0;
logic [7:0] acc_out   = '0;
logic [7:0] marl_out  = '0;
logic [7:0] marh_out  = '0;
logic [7:0] prl_out   = '0;
logic [7:0] prh_out   = '0;
logic [15:0] pc_addr;

logic reg_a_we = '0;
logic reg_b_we = '0;
logic reg_d_we = '0;
logic acc_we   = '0;
logic marl_we  = '0;
logic marh_we  = '0;
logic prl_we   = '0;
logic prh_we   = '0;
logic mem_we   = '0;

logic [7:0] bus;
logic [7:0] mem_data_out;
logic [15:0] mar_addr;
assign mar_addr = {marh_out, marl_out};

control_pkg::ctrl_t control_pins;

// ============================================
// Memory Subsystem
// ============================================

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

// ============================================
// Bus Selector
// ============================================

bus_selector bus_selector_i(
    .sel(control_pins.ssel),
    .a(reg_a_out),
    .d(reg_d_out),
    .b(reg_b_out),
    .acc(acc_out),
    .pcl(pc_addr[7:0]),
    .pch(pc_addr[15:8]),
    .m(mem_data_out),
    .out(bus)
);

reg_cell #(.W(8)) reg_a(
    .clk(clk),
    .rst_n(rst_n),
    .we(reg_a_we),
    .oe(1'b1),
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

reg_cell #(.W(8)) marl(
    .clk(clk),
    .rst_n(rst_n),
    .we(marl_we),
    .oe(1'b1),
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

alu alu_i(
    .a(reg_d_out),
    .b(bus),
    .ops(control_pins.ops),
    .negative(control_pins.sn),
    .c_in(c_reg_out),
    .result(alu_out),
    .carry_flag(c_reg_out)
);

assign carry_flag = alu_carry_out;

jump_logic jump_decoder(
    .jmp_en(control_pins.jmp),
    .carry_flag(control_pins.sc),
    .equal_flag(eq_reg_out),
    .greater_flag(gt_reg_out),
    .less_flag(lf_reg_out),
    .jmp_cond(jmp_select),
    .jmp_taken(jump_taken)
);

endmodule