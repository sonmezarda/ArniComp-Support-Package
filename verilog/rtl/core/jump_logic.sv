`timescale 1ns/1ps

module jump_logic(
    input  logic jmp_en,
    input  logic jgt,
    input  logic zero_flag,
    input  logic negative_flag,
    input  logic overflow_flag,
    input  logic carry_flag,
    input  logic [2:0] jmp_cond,
    output logic jmp_taken
);

    always_comb begin
        jmp_taken = 1'b0;

        if (jmp_en) begin
            if (jgt) begin
                jmp_taken = ~zero_flag & ~(negative_flag ^ overflow_flag); // JGT
            end else begin
                case (jmp_cond)
                    3'b000: jmp_taken = zero_flag;                         // JEQ
                    3'b001: jmp_taken = ~zero_flag;                        // JNE
                    3'b010: jmp_taken = carry_flag;                        // JCS
                    3'b011: jmp_taken = ~carry_flag;                       // JCC
                    3'b100: jmp_taken = negative_flag;                     // JMI
                    3'b101: jmp_taken = overflow_flag;                     // JVS
                    3'b110: jmp_taken = negative_flag ^ overflow_flag;     // JLT
                    3'b111: jmp_taken = 1'b1;                              // JMP
                    default: jmp_taken = 1'b0;
                endcase
            end
        end
    end


endmodule
