`timescale 1ns/1ps

// Test for Memory operations (MOV M,src and MOV dst,M)
module tb_memory;

    logic clk = 0;
    logic rst_n = 0;
    logic [15:0] mem_addr;
    logic [7:0] mem_rdata;
    logic [7:0] mem_wdata;
    logic mem_wen;
    logic mem_ren;

    always #5000 clk = ~clk;

    arnicomp_top #(
        .PROG_MEM_FILE("sim/tb_memory.mem")
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
        $dumpfile("wave_memory.vcd");
        $dumpvars(0, tb_memory);

        $display("\n========================================");
        $display("ArniComp Memory Operation Tests");
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
        $display("MARL = 0x%02X", dut.marl_out);
        $display("MARH = 0x%02X", dut.marh_out);

        $display("\n--- Checking Expected Values ---\n");
        
        // Test: Write 0x55 to memory[0x10], read it back to RB
        // Then write 0xAA to memory[0x11], read it back to RD
        
        check_reg("RB", dut.reg_b_out, 8'h55);  // Read from memory[0x10]
        check_reg("RD", dut.reg_d_out, 8'hAA);  // Read from memory[0x11]

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
