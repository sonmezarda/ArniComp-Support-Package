module bus_selector(
    input  logic [2:0] sel,
    input  logic [7:0] a,
    input  logic [7:0] d,
    input  logic [7:0] b,
    input  logic [7:0] acc,
    input  logic       out_en, 
    input  logic [7:0] pcl,
    input  logic [7:0] pch,
    input  logic [7:0] m,

    output logic [7:0] out
);

logic [7:0] out_sel;
// Source register encoding (from assembler):
// 000: RA, 001: RD, 010: RB, 011: ACC, 100: PCL, 101: PCH, 111: M
always_comb begin
    case(sel)
        3'b000: out_sel = a;      // RA
        3'b001: out_sel = d;      // RD
        3'b010: out_sel = b;      // RB
        3'b011: out_sel = acc;    // ACC
        3'b100: out_sel = pcl;    // PCL
        3'b101: out_sel = pch;    // PCH
        3'b110: out_sel = 8'h00;  // (unused)
        3'b111: out_sel = m;      // M
        default: out_sel = 8'h00;
    endcase
end

assign out = out_en ? out_sel : 8'd0;
endmodule
