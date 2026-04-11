`timescale 1ns/1ps

module tang_nano_9k_top (
    input  logic       clk,
    input  logic       rst_n,
    input  logic       btn_run,
    input  logic       uart_rx,
    inout  tri         i2c_scl,
    inout  tri         i2c_sda,
    inout  tri   [7:0] gpio,
    output logic [5:0] led,
    output logic       uart_tx
);

    localparam int CLK_DIV = 135;
    localparam int CLK_COUNTER_W = (CLK_DIV <= 1) ? 1 : $clog2(CLK_DIV);

    logic [CLK_COUNTER_W-1:0] clk_counter;
    logic cpu_clk;

    generate
        if (CLK_DIV <= 1) begin : gen_cpu_clk_direct
            always_comb begin
                cpu_clk = clk;
            end
        end else begin : gen_cpu_clk_div
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
        end
    endgenerate

    logic [15:0] debounce_counter;
    logic rst_n_sync, rst_n_debounced;
    logic btn_run_sync, btn_run_debounced;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rst_n_sync <= 1'b0;
            btn_run_sync <= 1'b1;
        end else begin
            rst_n_sync <= rst_n;
            btn_run_sync <= btn_run;
        end
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            debounce_counter <= '0;
            rst_n_debounced <= 1'b0;
            btn_run_debounced <= 1'b1;
        end else begin
            if (debounce_counter < 16'hFFFF) begin
                debounce_counter <= debounce_counter + 1;
            end else begin
                debounce_counter <= '0;
                rst_n_debounced <= rst_n_sync;
                btn_run_debounced <= btn_run_sync;
            end
        end
    end

    logic [7:0] debug_led;

    arnicomp_soc_top_gowin #(
        .GPIO_WIDTH(8)
    ) soc (
        .cpu_clk(cpu_clk),
        .uart_clk(clk),
        .pwm_clk(clk),
        .rst_n(rst_n_debounced),
        .uart_rx(uart_rx),
        .i2c_scl(i2c_scl),
        .i2c_sda(i2c_sda),
        .gpio(gpio),
        .uart_tx(uart_tx),
        .debug_led(debug_led)
    );

    assign led = ~debug_led[5:0];

endmodule
