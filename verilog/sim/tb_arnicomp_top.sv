`timescale 1ns/1ps

module tb_arnicomp_top;

    logic clk;
    logic rst_n;
    logic [15:0] mem_addr;
    logic [7:0] mem_rdata;
    logic [7:0] mem_wdata;
    logic mem_wen;
    logic mem_ren;

    // Clock generation: 10ns period (100MHz)
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    // DUT instantiation
    arnicomp_top #(
        .PROG_MEM_FILE("sim/tb_program.mem")
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

    // VCD dump for waveform viewing
    initial begin
        $dumpfile("wave.vcd");
        $dumpvars(0, tb_arnicomp_top);
    end

    // Test sequence
    initial begin
        $display("=== ArniComp Top Testbench ===");
        $display("Time: %0t - Starting test", $time);

        // Reset sequence
        rst_n = 0;
        repeat(5) @(posedge clk);
        rst_n = 1;
        $display("Time: %0t - Reset released", $time);

        // Run for some cycles
        repeat(20) @(posedge clk);

        // Monitor registers
        $display("\n=== Final Register State ===");
        $display("PC     = 0x%04X", dut.pc_addr);
        $display("RA     = 0x%02X", dut.reg_a_out);
        $display("RD     = 0x%02X", dut.reg_d_out);
        $display("RB     = 0x%02X", dut.reg_b_out);
        $display("ACC    = 0x%02X", dut.acc_out);
        $display("MARL   = 0x%02X", dut.marl_out);
        $display("MARH   = 0x%02X", dut.marh_out);
        $display("PRL    = 0x%02X", dut.prl_out);
        $display("PRH    = 0x%02X", dut.prh_out);
        $display("Flags: Z=%b N=%b C=%b V=%b", 
                 dut.z_reg_out, dut.n_reg_out, dut.c_reg_out, dut.v_reg_out);

        $display("\n=== Test Complete ===");
        $finish;
    end

    // Timeout watchdog
    initial begin
        #10000;
        $display("ERROR: Test timeout!");
        $finish;
    end

    // Optional: Monitor PC changes
    always @(posedge clk) begin
        if (rst_n) begin
            $display("Time: %0t | PC: %04X | Inst: %02X | we=%b accw=%b | bus=%02X RA=%02X ACC=%02X", 
                     $time, dut.pc_addr, dut.inst_q, 
                     dut.control_pins.we, dut.control_pins.accw,
                     dut.bus, dut.reg_a_out, dut.acc_out);
        end
    end

endmodule
