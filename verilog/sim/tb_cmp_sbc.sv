`timescale 1ns/1ps

// Test for CMP and SBC instructions
module tb_cmp_sbc;

    logic clk = 0;
    logic rst_n = 0;

    always #5000 clk = ~clk;

    arnicomp_top #(
        .PROG_MEM_FILE("sim/tb_cmp_sbc.mem")
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

    task automatic check_flag(string name, logic actual, logic expected);
        if (actual === expected) begin
            $display("  [PASS] %s = %b (expected %b)", name, actual, expected);
            pass_count++;
        end else begin
            $display("  [FAIL] %s = %b (expected %b)", name, actual, expected);
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
        $dumpfile("wave_cmp_sbc.vcd");
        $dumpvars(0, tb_cmp_sbc);

        $display("\n========================================");
        $display("ArniComp CMP and SBC Instruction Tests");
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
        $display("Flags: LT=%b EQ=%b GT=%b C=%b", 
                 dut.lf_reg_out, dut.eq_reg_out, dut.gt_reg_out, dut.c_reg_out);

        $display("\n--- Checking Expected Values ---\n");
        
        // CMP tests set flags without changing registers
        // SBC: ACC = RD - RA - !C
        // Test: RD=20, RA=5, C=1 (from overflow), SBC -> 20 - 5 - 0 = 15
        
        check_reg("RB", dut.reg_b_out, 8'h0F);  // SBC result: 20 - 5 - !C = 15
        check_flag("GT", dut.gt_reg_out, 1'b1); // Final CMP: 20 > 5

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
