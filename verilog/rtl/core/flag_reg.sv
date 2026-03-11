module flag_reg(
    input  logic clk,
    input  logic we,
    input  logic rst_n,
    input  logic lt_f_in,
    input  logic eq_f_in,
    input  logic gt_f_in,
    input  logic c_f_in,
    output logic lt_f_out,
    output logic eq_f_out,
    output logic gt_f_out,
    output logic c_f_out
);

reg_cell #(
    .W(4)
)flag_register(
    .clk(clk),
    .rst_n(rst_n),
    .we(we),
    .oe(1'b1),
    .d({lt_f_in, eq_f_in, gt_f_in, c_f_in}),
    .out({lt_f_out, eq_f_out, gt_f_out, c_f_out})
);

endmodule
