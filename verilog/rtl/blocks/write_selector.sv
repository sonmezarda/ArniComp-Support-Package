module write_selector(
    input  logic [2:0] write_sel,
    output logic a,
    output logic d,
    output logic b,
    output logic marl,
    output logic marh,
    output logic prl,
    output logic prh,
    output logic m
);

always_comb begin
    a    = 1'b0;
    d    = 1'b0;
    b    = 1'b0;
    marl = 1'b0;
    marh = 1'b0;
    prl  = 1'b0;
    prh  = 1'b0;
    m    = 1'b0;

    case (write_sel)
        3'b000: a    = 1'b1;
        3'b001: d    = 1'b1;
        3'b010: b    = 1'b1;
        3'b011: marl = 1'b1;
        3'b100: marh = 1'b1;
        3'b101: prl  = 1'b1;
        3'b110: prh  = 1'b1;
        3'b111: m    = 1'b1;
        default: ;
    endcase
end

endmodule
