`timescale 1ps/1ps

module tb_program_counter;

    logic clk;
    logic rst_n;
    logic count_en;
    logic load_en;
    logic [15:0] load_data;
    logic [15:0] paddr;

    program_counter dut (
        .clk(clk),
        .rst_n(rst_n),
        .count_en(count_en),
        .load_en(load_en),
        .load_data(load_data),
        .paddr(paddr)
    );

    initial clk = 1'b0;
    always #5 clk = ~clk;

    task automatic tick;
        begin
            @(posedge clk);
            #1;
        end
    endtask

    initial begin
        $display("Starting program_counter test");

        rst_n = 1'b1;
        count_en = 1'b0;
        load_en = 1'b0;
        load_data = 16'h0000;

        // Async reset
        rst_n = 1'b0;
        #1;
        if (paddr !== 16'h0000) $fatal(1, "reset failed: paddr=%h", paddr);
        rst_n = 1'b1;
        #1;

        // Hold when disabled
        tick();
        if (paddr !== 16'h0000) $fatal(1, "hold failed: paddr=%h", paddr);

        // Count
        count_en = 1'b1;
        tick();
        if (paddr !== 16'h0001) $fatal(1, "count 1 failed: paddr=%h", paddr);
        tick();
        if (paddr !== 16'h0002) $fatal(1, "count 2 failed: paddr=%h", paddr);

        // Load takes priority over count
        load_data = 16'h1234;
        load_en = 1'b1;
        count_en = 1'b1;
        tick();
        if (paddr !== 16'h1234) $fatal(1, "load priority failed: paddr=%h", paddr);

        // Continue counting from loaded value
        load_en = 1'b0;
        count_en = 1'b1;
        tick();
        if (paddr !== 16'h1235) $fatal(1, "count after load failed: paddr=%h", paddr);

        // Wraparound check
        load_data = 16'hFFFF;
        load_en = 1'b1;
        count_en = 1'b0;
        tick();
        if (paddr !== 16'hFFFF) $fatal(1, "load FFFF failed: paddr=%h", paddr);

        load_en = 1'b0;
        count_en = 1'b1;
        tick();
        if (paddr !== 16'h0000) $fatal(1, "wraparound failed: paddr=%h", paddr);

        $display("PASS: tb_program_counter OK");
        $finish;
    end

endmodule
