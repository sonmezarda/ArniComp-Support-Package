`timescale 1ns/1ps

module alu(
    input  logic [7:0] a,
    input  logic [7:0] b,
    input  logic [1:0] ops,
    input  logic       negative,
    input  logic       c_in, // carry in
    output logic [7:0] result,
    output logic       carry_flag
);

    logic [7:0] sum;
    logic       carry_out;
    logic [8:0] arith_tmp;

    always_comb begin
        sum = '0;
        carry_out = 1'b0;
        arith_tmp = '0;

        case(ops)
            2'b00:
                if (!negative) begin
                    arith_tmp = {1'b0, a} + {1'b0, b} + {8'b0, c_in};
                    carry_out = arith_tmp[8];
                    sum = arith_tmp[7:0];
                end else begin
                    arith_tmp = {1'b0, a} - {1'b0, b} - {8'b0, ~c_in};
                    carry_out = ~arith_tmp[8];
                    sum = arith_tmp[7:0];
                end
            2'b01: sum = a & b;
            2'b10: sum = a ^ b;
            2'b11: sum = ~b;  // NOT uses b input (source on bus)
        endcase
    end

    assign result = sum;
    assign carry_flag = carry_out;
endmodule 
