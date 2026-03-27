`timescale 1ns/1ps
//
// Tang Nano 9K Top-Level Wrapper for ArniComp CPU
// 
// Features:
// - Clock divider (27MHz -> configurable CPU clock)
// - Button debouncing
// - LED debug output (ACC lower 6 bits)
// - Single-step mode support
//

module tang_nano_9k_first_test_top (
    input  logic       clk,        // 27MHz system clock
    input  logic       rst_n,      // Reset button (active low)
    input  logic       btn_run,    // Run/single-step button (active low)
    output logic [5:0] led         // Onboard LEDs (active low)
);

    localparam CLK_DIV = 135000;
    
    logic [$clog2(CLK_DIV)-1:0] clk_counter;
    logic cpu_clk;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            clk_counter <= '0;
            cpu_clk <= 1'b0;
        end else begin
            if (clk_counter >= CLK_DIV - 1) begin
                clk_counter <= '0;
                cpu_clk <= ~cpu_clk;
            end else begin
                clk_counter <= clk_counter + 1;
            end
        end
    end
    
    logic [15:0] debounce_counter;
    logic rst_n_sync, rst_n_debounced;
    logic btn_run_sync, btn_run_debounced;
    
    always_ff @(posedge clk) begin
        rst_n_sync <= rst_n;
        btn_run_sync <= btn_run;
    end
    
    always_ff @(posedge clk) begin
        if (debounce_counter < 16'hFFFF) begin
            debounce_counter <= debounce_counter + 1;
        end else begin
            debounce_counter <= '0;
            rst_n_debounced <= rst_n_sync;
            btn_run_debounced <= btn_run_sync;
        end
    end

    logic [15:0] mem_addr;
    logic [7:0]  mem_rdata;
    logic [7:0]  mem_wdata;
    logic mem_we;

    logic [7:0] data_mem_dout;
    logic [7:0] led_reg_dout;
    logic data_mem_sel;
    logic led_reg_sel;
    logic data_mem_we;
    logic led_reg_we;

    assign data_mem_sel = (mem_addr[15:8] == 8'h00);
    assign led_reg_sel  = (mem_addr[15:8] == 8'h01);
    assign data_mem_we  = mem_we && data_mem_sel;
    assign led_reg_we   = mem_we && led_reg_sel;

    assign mem_rdata = data_mem_sel ? data_mem_dout :
                       led_reg_sel  ? led_reg_dout :
                       8'h00;

    arnicomp_top #(
        .PROG_MEM_FILE("rom/program.mem")
    ) cpu (
        .clk(cpu_clk),
        .rst_n(rst_n_debounced),
        .mem_rdata(mem_rdata),
        .mem_addr(mem_addr),
        .mem_wdata(mem_wdata),
        .mem_wen(mem_we)
    );

    data_memory #(.MEM_SIZE(256)) data_mem (
        .clk(cpu_clk),
        .we(data_mem_we),
        .addr(mem_addr),
        .data_in(mem_wdata),
        .data_out(data_mem_dout)
    );

    reg_cell led_reg(
        .clk(cpu_clk),
        .rst_n(rst_n_debounced),
        .we(led_reg_we),
        .oe(1'b1),
        .d(mem_wdata),
        .out(led_reg_dout)

    );
    
    assign led = ~led_reg_dout[5:0];
    
endmodule
