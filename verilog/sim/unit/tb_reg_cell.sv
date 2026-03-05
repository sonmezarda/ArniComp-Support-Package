`timescale 1ns/1ps

module tb_reg_cell;

    localparam int W = 8;

    logic clk;
    logic rst_n;
    logic we;
    logic oe;
    logic [W-1:0] d;
    logic [W-1:0] out;

    reg_cell #(.W(W), .RESET_VALUE('0)) dut (
        .clk  (clk),
        .rst_n(rst_n),
        .we   (we),
        .oe   (oe),
        .d    (d),
        .out  (out)
    );

    initial clk = 0;
    always #5 clk <= ~clk;

    task tick;
        @(posedge clk);
        #1; 
    endtask

    

    initial begin
        rst_n = 1;
        we    = 0;
        oe    = 1;
        d     = '0;

        // write test
        d  = 8'hAB;
        we = 1;
        tick();
        if (out !== 8'hAB) $fatal(1, "write AB failed. out=%h", out);

        // async reset test
        rst_n = 0;       
        #1;              
        if (out !== 8'h00) $fatal(1, "async reset failed. out=%h", out);

        rst_n = 1;    
        #1;

        // 2) we=0 hold test
        we = 0;
        d  = 8'h55;
        tick();
        if (out !== 8'h00) $fatal(1, "hold failed. out=%h", out);

        // 3) write test
        we = 1;
        d  = 8'h12;
        tick();
        if (out !== 8'h12) $fatal(1, "write 12 failed. out=%h", out);

        d  = 8'h34;
        tick();
        if (out !== 8'h34) $fatal(1, "write 34 failed. out=%h", out);

        // 4) oe gating
        oe = 0;
        #1;
        if (out !== 8'h00) $fatal(1, "oe=0 gating failed. out=%h", out);

        oe = 1;
        #1;
        if (out !== 8'h34) $fatal(1, "oe=1 ungate failed. out=%h", out);

        $display("PASS: tb_reg_cell OK");
        $finish;
    end

    initial begin
        $dumpfile("wave.vcd");
        $dumpvars(0, tb_reg_cell);
    end
endmodule
