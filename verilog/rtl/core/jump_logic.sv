`timescale 1ns/1ps

module jump_logic(
    input logic jmp_en,
    input logic carry_flag,
    input logic equal_flag,
    input logic greater_flag,
    input logic less_flag,
    input logic [2:0] jmp_cond,
    output logic jmp_taken
);

    always_comb begin
        jmp_taken = 1'b0;

        if (jmp_en) begin
            case (jmp_cond)
                3'b000: jmp_taken = 1'b1;                         // JMP
                3'b001: jmp_taken = equal_flag;                   // JEQ
                3'b010: jmp_taken = greater_flag;                 // JGT
                3'b011: jmp_taken = less_flag;                    // JLT
                3'b100: jmp_taken = greater_flag | equal_flag;    // JGE
                3'b101: jmp_taken = less_flag | equal_flag;       // JLE
                3'b110: jmp_taken = ~equal_flag;                  // JNE
                3'b111: jmp_taken = carry_flag;                   // JC
                default: jmp_taken = 1'b0;
            endcase
        end
    end


endmodule
