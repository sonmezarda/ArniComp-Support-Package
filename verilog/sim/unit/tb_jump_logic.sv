`timescale 1ns/1ps

module tb_jump_logic;

    logic jmp_en;
    logic carry_flag;
    logic equal_flag;
    logic greater_flag;
    logic less_flag;
    logic [2:0] jmp_cond;
    logic jmp_taken;

    jump_logic dut (
        .jmp_en(jmp_en),
        .carry_flag(carry_flag),
        .equal_flag(equal_flag),
        .greater_flag(greater_flag),
        .less_flag(less_flag),
        .jmp_cond(jmp_cond),
        .jmp_taken(jmp_taken)
    );

    task automatic check_case(
        input logic       jmp_en_i,
        input logic       c_i,
        input logic       e_i,
        input logic       g_i,
        input logic       l_i,
        input logic [2:0] cond_i,
        input logic       exp_taken,
        input string      name
    );
        begin
            jmp_en = jmp_en_i;
            carry_flag = c_i;
            equal_flag = e_i;
            greater_flag = g_i;
            less_flag = l_i;
            jmp_cond = cond_i;
            #1;

            if (jmp_taken !== exp_taken) begin
                $fatal(
                    1,
                    "%s failed: en=%b c=%b e=%b g=%b l=%b cond=%b -> taken=%b (exp=%b)",
                    name, jmp_en, carry_flag, equal_flag, greater_flag, less_flag, jmp_cond, jmp_taken, exp_taken
                );
            end
        end
    endtask

    initial begin
        $display("Starting jump_logic test");

        // jmp_en gate
        check_case(1'b0, 1'b1, 1'b1, 1'b1, 1'b1, 3'b000, 1'b0, "gate off");

        // Emulator mapping:
        // 000 JMP, 001 JEQ, 010 JGT, 011 JLT, 100 JGE, 101 JLE, 110 JNE, 111 JC
        check_case(1'b1, 1'b0, 1'b0, 1'b0, 1'b0, 3'b000, 1'b1, "JMP");
        check_case(1'b1, 1'b0, 1'b1, 1'b0, 1'b0, 3'b001, 1'b1, "JEQ true");
        check_case(1'b1, 1'b0, 1'b0, 1'b0, 1'b0, 3'b001, 1'b0, "JEQ false");
        check_case(1'b1, 1'b0, 1'b0, 1'b1, 1'b0, 3'b010, 1'b1, "JGT true");
        check_case(1'b1, 1'b0, 1'b0, 1'b0, 1'b1, 3'b011, 1'b1, "JLT true");
        check_case(1'b1, 1'b0, 1'b1, 1'b0, 1'b0, 3'b100, 1'b1, "JGE eq");
        check_case(1'b1, 1'b0, 1'b0, 1'b1, 1'b0, 3'b100, 1'b1, "JGE gt");
        check_case(1'b1, 1'b0, 1'b0, 1'b0, 1'b1, 3'b100, 1'b0, "JGE false");
        check_case(1'b1, 1'b0, 1'b1, 1'b0, 1'b0, 3'b101, 1'b1, "JLE eq");
        check_case(1'b1, 1'b0, 1'b0, 1'b0, 1'b1, 3'b101, 1'b1, "JLE lt");
        check_case(1'b1, 1'b0, 1'b0, 1'b1, 1'b0, 3'b101, 1'b0, "JLE false");
        check_case(1'b1, 1'b0, 1'b0, 1'b0, 1'b0, 3'b110, 1'b1, "JNE true");
        check_case(1'b1, 1'b0, 1'b1, 1'b0, 1'b0, 3'b110, 1'b0, "JNE false");
        check_case(1'b1, 1'b1, 1'b0, 1'b0, 1'b0, 3'b111, 1'b1, "JC true");
        check_case(1'b1, 1'b0, 1'b0, 1'b0, 1'b0, 3'b111, 1'b0, "JC false");

        $display("PASS: tb_jump_logic OK");
        $finish;
    end

endmodule
