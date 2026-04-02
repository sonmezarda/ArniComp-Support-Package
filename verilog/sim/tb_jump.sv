`timescale 1ns/1ps

// Test for Jump instructions
module tb_jump;

    logic clk = 0;
    logic rst_n = 0;
    logic [15:0] mem_addr;
    logic [7:0] mem_rdata;
    logic [7:0] mem_wdata;
    logic mem_wen;
    logic mem_ren;

    always #5000 clk = ~clk;

    arnicomp_top #(
        .PROG_MEM_FILE("sim/tb_jump.mem")
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
        $dumpfile("wave_jump.vcd");
        $dumpvars(0, tb_jump);

        $display("\n========================================");
        $display("ArniComp Jump Instruction Tests");
        $display("========================================\n");

        rst_n = 0;
        repeat(5) @(posedge clk);
        rst_n = 1;
        @(posedge clk);

        wait_for_halt();

        $display("\n--- Final Register State ---");
        $display("PC   = 0x%04X", dut.pc_addr);
        $display("RA   = 0x%02X", dut.reg_a_out);
        $display("RD   = 0x%02X", dut.reg_d_out);
        $display("RB   = 0x%02X", dut.reg_b_out);
        $display("ACC  = 0x%02X", dut.acc_out);
        $display("Flags: Z=%b N=%b C=%b V=%b", 
                 dut.z_reg_out, dut.n_reg_out, dut.c_reg_out, dut.v_reg_out);

        $display("\n--- Checking Expected Values ---\n");
        
        // Test results depend on execution path
        // JMP should skip to address 0x10, set RA=0x11
        // JEQ should be taken when EQ=1, set RB=0x22
        // JNE should NOT be taken when EQ=1
        // Final: RA=0x11, RB=0x22, RD=0x33
        
        check_reg("RA", dut.reg_a_out, 8'h11);  // Set after JMP
        check_reg("RB", dut.reg_b_out, 8'h22);  // Set after JEQ taken
        check_reg("RD", dut.reg_d_out, 8'h33);  // Set at end

        $display("\n========================================");
        $display("Test Summary: %0d passed, %0d failed", pass_count, fail_count);
        $display("========================================\n");

        $finish;
    end

    initial begin
        #10000000;
        $display("ERROR: Test timeout!");
        $finish;
    end

endmodule
