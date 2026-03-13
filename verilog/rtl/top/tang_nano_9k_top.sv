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

module tang_nano_9k_top (
    input  logic       clk,        // 27MHz system clock
    input  logic       rst_n,      // Reset button (active low)
    input  logic       btn_run,    // Run/single-step button (active low)
    output logic [5:0] led        // Onboard LEDs (active low)
);

    // ========================================
    // Parameters
    // ========================================
    
    // Clock divider: 27MHz / (2 * CLK_DIV) = CPU clock
    // CLK_DIV = 13500000 -> 1 Hz (for visible LED blinking)
    // CLK_DIV = 135000   -> 100 Hz (slow visible execution)
    // CLK_DIV = 1350     -> 10 kHz (moderate speed)
    // CLK_DIV = 1        -> 13.5 MHz (full speed)
    localparam CLK_DIV = 135000;  // 100 Hz by default
    
    // ========================================
    // Clock Divider
    // ========================================
    
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
    
    // ========================================
    // Button Debouncing
    // ========================================
    
    logic [15:0] debounce_counter;
    logic rst_n_sync, rst_n_debounced;
    logic btn_run_sync, btn_run_debounced;
    
    // Synchronize buttons to clock domain
    always_ff @(posedge clk) begin
        rst_n_sync <= rst_n;
        btn_run_sync <= btn_run;
    end
    
    // Simple debounce (hold for ~2ms at 27MHz)
    always_ff @(posedge clk) begin
        if (debounce_counter < 16'hFFFF) begin
            debounce_counter <= debounce_counter + 1;
        end else begin
            debounce_counter <= '0;
            rst_n_debounced <= rst_n_sync;
            btn_run_debounced <= btn_run_sync;
        end
    end

    // The program is loaded from rom/program.mem at synthesis time
    
    logic [16:0] mem_addr;
    logic [7:0]  mem_rdata;
    logic [7:0]  mem_wdata;
    logic mem_we;

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

    data_memory data_mem (
        .clk(clk),
        .we(mem_we),
        .addr(mem_addr),
        .data_in(mem_wdata),
        .data_out(mem_rdata)
    );
    
    // LED Output (active low)

    assign led = ~cpu.acc_out[5:0];
    

endmodule
