module bus_selector(
    input  logic [2:0] sel,
    input  logic [7:0] a,
    input  logic [7:0] d,
    input  logic [7:0] b,
    input  logic [7:0] acc,
    
    input  logic [7:0] pcl,
    input  logic [7:0] pch,
    input  logic [7:0] m,

    output logic [7:0] out
);

logic [7:0] out_sel;
always_comb begin
    case(sel)
        3'b000: out_sel = a;
        3'b001: out_sel = d;
        3'b010: out_sel = b;
        3'b011: out_sel = acc; 
        3'b100: out_sel = 8'h00;
        3'b101: out_sel = pcl;
        3'b110: out_sel = pch;
        3'b111: out_sel = m;
        default: out_sel = 8'h00;
    endcase
end

assign out = out_sel;
endmodule
