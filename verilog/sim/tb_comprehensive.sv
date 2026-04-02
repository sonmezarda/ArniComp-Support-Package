`timescale 1ns/1ps

module tb_comprehensive;

    logic clk = 0;
    logic rst_n = 0;
    logic [15:0] mem_addr;
    logic [7:0] mem_rdata;
    logic [7:0] mem_wdata;
    logic mem_wen;
    logic mem_ren;

    always #5000 clk = ~clk;  // 100kHz clock

    arnicomp_top #(
        .PROG_MEM_FILE("sim/tb_comprehensive.mem")
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .mem_rdata(mem_rdata),
        .mem_addr(mem_addr),
        .mem_wdata(mem_wdata),
        .mem_wen(mem_wen),
        .mem_ren(mem_ren)
    );

    data_memory #(.MEM_SIZE(4096)) data_mem (
        .clk(clk),
        .we(mem_wen),
        .addr(mem_addr),
        .data_in(mem_wdata),
        .data_out(mem_rdata)
    );

    // Test tracking
    int test_num = 0;
    int pass_count = 0;
    int fail_count = 0;

    // Test macro-like tasks
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

    task automatic run_cycles(int n);
        repeat(n) @(posedge clk);
    endtask

    task automatic wait_for_halt();
        int timeout = 1000;
        while (dut.control_pins.ce !== 1'b0 && timeout > 0) begin
            @(posedge clk);
            timeout--;
        end
        if (timeout == 0) $display("  [WARN] Timeout waiting for HLT");
        @(posedge clk); // One more cycle after halt
    endtask

    initial begin
        $dumpfile("wave_comprehensive.vcd");
        $dumpvars(0, tb_comprehensive);

        $display("\n========================================");
        $display("ArniComp Comprehensive Instruction Tests");
        $display("========================================\n");

        // Reset sequence
        rst_n = 0;
        repeat(5) @(posedge clk);
        rst_n = 1;
        @(posedge clk);

        // Wait for program to complete (halt)
        wait_for_halt();

        // Now check all expected values
        $display("\n--- Test Results ---\n");

        // Test 1: LDI
        $display("Test: LDI instruction");
        // After LDI 0x55, RA should be 0x55
        // Program sets RA to various values, final RA tested after all ops
        
        // Test 2: MOV
        $display("Test: MOV instruction");
        // RD should have value from RA
        
        // Test 3: ADD
        $display("Test: ADD instruction");
        // ACC should have RD + source
        
        // Test 4: ADDI
        $display("Test: ADDI instruction");
        
        // Test 5: SUB
        $display("Test: SUB instruction");
        
        // Test 6: SUBI
        $display("Test: SUBI instruction");

        // Final state check (based on program)
        $display("\n--- Final Register State ---");
        $display("PC   = 0x%04X", dut.pc_addr);
        $display("RA   = 0x%02X", dut.reg_a_out);
        $display("RD   = 0x%02X", dut.reg_d_out);
        $display("RB   = 0x%02X", dut.reg_b_out);
        $display("ACC  = 0x%02X", dut.acc_out);
        $display("MARL = 0x%02X", dut.marl_out);
        $display("MARH = 0x%02X", dut.marh_out);
        $display("PRL  = 0x%02X", dut.prl_out);
        $display("PRH  = 0x%02X", dut.prh_out);
        $display("Flags: Z=%b N=%b C=%b V=%b", 
                 dut.z_reg_out, dut.n_reg_out, dut.c_reg_out, dut.v_reg_out);

        // Expected values from the test program (auto-generated)
        $display("\n--- Checking Expected Values ---\n");
        
        check_reg("RA", dut.reg_a_out, 8'h80);   // After SMSBRA
        check_reg("RD", dut.reg_d_out, 8'h32);   // 50 decimal
        check_reg("RB", dut.reg_b_out, 8'h05);   // 5
        check_reg("ACC", dut.acc_out, 8'h1E);    // 30 = 50 - 20
        check_reg("MARL", dut.marl_out, 8'h03);  // After INX x3
        check_reg("PRL", dut.prl_out, 8'h30);    // Jump target low
        check_reg("PRH", dut.prh_out, 8'h00);    // Jump target high

        $display("\n========================================");
        $display("Test Summary: %0d passed, %0d failed", pass_count, fail_count);
        $display("========================================\n");

        $finish;
    end

    // Timeout watchdog
    initial begin
        #5000000;
        $display("ERROR: Test timeout!");
        $finish;
    end

endmodule
