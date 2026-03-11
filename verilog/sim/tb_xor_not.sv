`timescale 1ns/1ps

// Test for XOR and NOT instructions
module tb_xor_not;

    logic clk = 0;
    logic rst_n = 0;

    always #5000 clk = ~clk;

    arnicomp_top #(
        .PROG_MEM_FILE("sim/tb_xor_not.mem")
    ) dut (
        .clk(clk),
        .rst_n(rst_n)
    );

    int pass_count = 0, fail_count = 0;

    task automatic check_reg(string name, logic [7:0] actual, logic [7:0] expected);
        if (actual === expected) begin
            $display("  [PASS] %s = 0x%02X (expected 0x%02X)", name, actual, expected);
            pass_count++;
        end else begin
            $display("  [FAIL] %s = 0x%02X (expected 0x%02X)", name, actual, expected);
            fail_count++;
        end
    endtask

    task automatic wait_for_halt();
        int timeout = 1000;
        while (dut.control_pins.ce !== 1'b0 && timeout > 0) begin
            @(posedge clk);
            timeout--;
        end
        @(posedge clk);
    endtask

    initial begin
        $dumpfile("wave_xor_not.vcd");
        $dumpvars(0, tb_xor_not);

        $display("\n========================================");
        $display("ArniComp XOR and NOT Instruction Tests");
        $display("========================================\n");

        rst_n = 0;
        repeat(5) @(posedge clk);
        rst_n = 1;
        @(posedge clk);

        wait_for_halt();

        $display("\n--- Final Register State ---");
        $display("RA   = 0x%02X", dut.reg_a_out);
        $display("RD   = 0x%02X", dut.reg_d_out);
        $display("RB   = 0x%02X", dut.reg_b_out);
        $display("ACC  = 0x%02X", dut.acc_out);

        $display("\n--- Checking Expected Values ---\n");
        
        // XOR: RA=0x0F, RD=0x7F -> ACC=0x70
        // NOT: RA=0x55 -> ACC=0xAA (stored in RB via MOV)
        // Final RA has NOT result moved from ACC
        
        check_reg("RB", dut.reg_b_out, 8'h70);   // XOR result: 0x7F ^ 0x0F = 0x70
        check_reg("RA", dut.reg_a_out, 8'hAA);   // NOT result: ~0x55 = 0xAA

        $display("\n========================================");
        $display("Test Summary: %0d passed, %0d failed", pass_count, fail_count);
        $display("========================================\n");

        $finish;
    end

    initial begin
        #5000000;
        $display("ERROR: Test timeout!");
        $finish;
    end

endmodule
