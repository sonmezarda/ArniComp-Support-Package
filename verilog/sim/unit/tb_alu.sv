`timescale 1ns/1ps

module tb_alu;

    logic [7:0] a;
    logic [7:0] b;
    logic [1:0] ops;
    logic       negative;
    logic       c_in;
    logic [7:0] result;
    logic       carry_flag;

    alu dut (
        .a(a),
        .b(b),
        .ops(ops),
        .negative(negative),
        .c_in(c_in),
        .result(result),
        .carry_flag(carry_flag)
    );

    task automatic check_case(
        input logic [7:0] a_i,
        input logic [7:0] b_i,
        input logic [1:0] ops_i,
        input logic       negative_i,
        input logic       c_in_i,
        input logic [7:0] exp_result,
        input logic       exp_carry,
        input string      name
    );
        begin
            a = a_i;
            b = b_i;
            ops = ops_i;
            negative = negative_i;
            c_in = c_in_i;
            #1;

            if (result !== exp_result || carry_flag !== exp_carry) begin
                $fatal(
                    1,
                    "%s failed: a=%h b=%h ops=%b neg=%b c_in=%b -> result=%h carry=%b (expected %h %b)",
                    name, a, b, ops, negative, c_in, result, carry_flag, exp_result, exp_carry
                );
            end
        end
    endtask

    initial begin
        $display("Starting ALU test");

        // ADD: c_in=0 -> a+b
        check_case(8'h10, 8'h20, 2'b00, 1'b0, 1'b0, 8'h30, 1'b0, "ADD basic");
        check_case(8'hFF, 8'h01, 2'b00, 1'b0, 1'b0, 8'h00, 1'b1, "ADD carry");

        // ADC: c_in=1 -> a+b+1
        check_case(8'h10, 8'h20, 2'b00, 1'b0, 1'b1, 8'h31, 1'b0, "ADC basic");
        check_case(8'hFF, 8'h00, 2'b00, 1'b0, 1'b1, 8'h00, 1'b1, "ADC carry");

        // SUB: c_in=1 means no extra borrow => a-b
        check_case(8'h20, 8'h10, 2'b00, 1'b1, 1'b1, 8'h10, 1'b1, "SUB no borrow");
        check_case(8'h10, 8'h20, 2'b00, 1'b1, 1'b1, 8'hF0, 1'b0, "SUB borrow");

        // SBC: c_in=1 -> a-b, c_in=0 -> a-b-1 (emulator-compatible)
        check_case(8'h20, 8'h10, 2'b00, 1'b1, 1'b0, 8'h0F, 1'b1, "SBC c_in0");
        check_case(8'h10, 8'h10, 2'b00, 1'b1, 1'b0, 8'hFF, 1'b0, "SBC borrow");

        // Bitwise ops
        check_case(8'hAA, 8'h0F, 2'b01, 1'b0, 1'b0, 8'h0A, 1'b0, "AND");
        check_case(8'hAA, 8'h0F, 2'b10, 1'b0, 1'b0, 8'hA5, 1'b0, "XOR");
        check_case(8'h55, 8'h00, 2'b11, 1'b0, 1'b0, 8'hAA, 1'b0, "NOT");

        $display("PASS: tb_alu OK");
        $finish;
    end

endmodule
