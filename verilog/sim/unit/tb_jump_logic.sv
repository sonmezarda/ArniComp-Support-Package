`timescale 1ns/1ps

module tb_jump_logic;

    logic jmp_en;
    logic jgt;
    logic zero_flag;
    logic negative_flag;
    logic overflow_flag;
    logic carry_flag;
    logic [2:0] jmp_cond;
    logic jmp_taken;

    jump_logic dut (
        .jmp_en(jmp_en),
        .jgt(jgt),
        .zero_flag(zero_flag),
        .negative_flag(negative_flag),
        .overflow_flag(overflow_flag),
        .carry_flag(carry_flag),
        .jmp_cond(jmp_cond),
        .jmp_taken(jmp_taken)
    );

    task automatic check_case(
        input logic       jmp_en_i,
        input logic       jgt_i,
        input logic       z_i,
        input logic       n_i,
        input logic       v_i,
        input logic       c_i,
        input logic [2:0] cond_i,
        input logic       exp_taken,
        input string      name
    );
        begin
            jmp_en = jmp_en_i;
            jgt = jgt_i;
            zero_flag = z_i;
            negative_flag = n_i;
            overflow_flag = v_i;
            carry_flag = c_i;
            jmp_cond = cond_i;
            #1;

            if (jmp_taken !== exp_taken) begin
                $fatal(
                    1,
                    "%s failed: en=%b jgt=%b z=%b n=%b v=%b c=%b cond=%b -> taken=%b (exp=%b)",
                    name, jmp_en, jgt, zero_flag, negative_flag, overflow_flag, carry_flag, jmp_cond, jmp_taken, exp_taken
                );
            end
        end
    endtask

    initial begin
        $display("Starting jump_logic test");

        // jmp_en gate
        check_case(1'b0, 1'b0, 1'b1, 1'b1, 1'b1, 1'b1, 3'b000, 1'b0, "gate off");

        // Final ISA jump mapping:
        // 000 JEQ, 001 JNE, 010 JCS, 011 JCC, 100 JMI, 101 JVS, 110 JLT, 111 JMP
        check_case(1'b1, 1'b0, 1'b1, 1'b0, 1'b0, 1'b0, 3'b000, 1'b1, "JEQ true");
        check_case(1'b1, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 3'b000, 1'b0, "JEQ false");
        check_case(1'b1, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 3'b001, 1'b1, "JNE true");
        check_case(1'b1, 1'b0, 1'b1, 1'b0, 1'b0, 1'b0, 3'b001, 1'b0, "JNE false");
        check_case(1'b1, 1'b0, 1'b0, 1'b0, 1'b0, 1'b1, 3'b010, 1'b1, "JCS true");
        check_case(1'b1, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 3'b010, 1'b0, "JCS false");
        check_case(1'b1, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 3'b011, 1'b1, "JCC true");
        check_case(1'b1, 1'b0, 1'b0, 1'b0, 1'b0, 1'b1, 3'b011, 1'b0, "JCC false");
        check_case(1'b1, 1'b0, 1'b0, 1'b1, 1'b0, 1'b0, 3'b100, 1'b1, "JMI true");
        check_case(1'b1, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 3'b100, 1'b0, "JMI false");
        check_case(1'b1, 1'b0, 1'b0, 1'b0, 1'b1, 1'b0, 3'b101, 1'b1, "JVS true");
        check_case(1'b1, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 3'b101, 1'b0, "JVS false");
        check_case(1'b1, 1'b0, 1'b0, 1'b1, 1'b0, 1'b0, 3'b110, 1'b1, "JLT true");
        check_case(1'b1, 1'b0, 1'b0, 1'b1, 1'b1, 1'b0, 3'b110, 1'b0, "JLT false");
        check_case(1'b1, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 3'b111, 1'b1, "JMP");
        check_case(1'b1, 1'b1, 1'b0, 1'b0, 1'b0, 1'b0, 3'b000, 1'b1, "JGT true");
        check_case(1'b1, 1'b1, 1'b1, 1'b0, 1'b0, 1'b0, 3'b000, 1'b0, "JGT false on zero");

        $display("PASS: tb_jump_logic OK");
        $finish;
    end

endmodule
