`timescale 1ns/1ps

module tb_lr_stack;

    logic clk = 0;
    logic rst_n = 0;
    logic [15:0] mem_addr;
    logic [7:0] mem_rdata;
    logic [7:0] mem_wdata;
    logic mem_wen;
    logic mem_ren;

    always #5000 clk = ~clk;

    arnicomp_top #(
        .PROG_MEM_FILE("sim/tb_lr_stack.mem")
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
        $dumpfile("wave_lr_stack.vcd");
        $dumpvars(0, tb_lr_stack);

        rst_n = 0;
        repeat(5) @(posedge clk);
        rst_n = 1;
        @(posedge clk);

        wait_for_halt();

        $display("\n--- Final Register State ---");
        $display("RB   = 0x%02X", dut.reg_b_out);
        $display("SP   = 0x%04X", dut.sp_out);
        $display("PC   = 0x%04X", dut.pc_addr);

        $display("\n--- Checking Expected Values ---\n");
        check_reg("RB", dut.reg_b_out, 8'h5A);
        if (dut.sp_out === 16'h0000) begin
            $display("  [PASS] SP restored to 0x0000");
            pass_count++;
        end else begin
            $display("  [FAIL] SP = 0x%04X (expected 0x0000)", dut.sp_out);
            fail_count++;
        end

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
