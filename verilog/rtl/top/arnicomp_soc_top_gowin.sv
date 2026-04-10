`timescale 1ns/1ps

module arnicomp_soc_top_gowin #(
    parameter int RAM_SIZE = 2048,
    parameter int STACK_SIZE = 256,
    parameter int GPIO_WIDTH = 8,
    parameter int PWM_DUTY_WIDTH = 12,
    parameter logic [15:0] STACK_BASE_ADDR = 16'h0D00,
    parameter logic [15:0] STACK_END_ADDR  = 16'h0DFF
)(
    input  logic       cpu_clk,
    input  logic       uart_clk,
    input  logic       pwm_clk,
    input  logic       rst_n,
    input  logic       uart_rx,
    inout  tri         i2c_scl,
    inout  tri         i2c_sda,
    inout  tri   [GPIO_WIDTH-1:0] gpio,

    output logic       uart_tx,
    output logic [7:0] debug_led
);

    localparam logic [7:0] SYS_LED_OFFSET = 8'h00;

    logic [15:0] mem_addr;
    logic [15:0] instr_addr;
    logic [7:0]  inst_rdata;
    logic [7:0]  mem_rdata;
    logic [7:0]  mem_wdata;
    logic        mem_wen;
    logic        mem_ren;

    logic        ram_sel;
    logic        gpio_sel;
    logic        uart_sel;
    logic        i2c_sel;
    logic        timer_sel;
    logic        sys_sel;
    logic        stack_sel;
    logic        invalid_sel;

    logic [7:0]  ram_rdata;
    logic [7:0]  stack_rdata;
    logic [7:0]  gpio_rdata;
    logic [7:0]  uart_rdata;
    logic [7:0]  i2c_rdata;
    logic [7:0]  sys_rdata;
    logic [7:0]  sys_led_reg_out;
    logic [GPIO_WIDTH-1:0] gpio_in;
    logic [GPIO_WIDTH-1:0] gpio_out;
    logic [GPIO_WIDTH-1:0] gpio_oe;
    logic        ram_we;
    logic        stack_we;
    logic        gpio_we;
    logic        gpio_re;
    logic        uart_we;
    logic        uart_re;
    logic        i2c_we;
    logic        i2c_re;
    logic        sys_led_we;
    logic        sys_led_sel;
    genvar       gpio_idx;

    arnicomp_top_gowin #(
        .STACK_PTR_RESET_VALUE(STACK_BASE_ADDR)
    ) cpu (
        .clk(cpu_clk),
        .rst_n(rst_n),
        .instr_rdata(inst_rdata),
        .mem_rdata(mem_rdata),
        .instr_addr(instr_addr),
        .mem_addr(mem_addr),
        .mem_wdata(mem_wdata),
        .mem_wen(mem_wen),
        .mem_ren(mem_ren)
    );

    Gowin_pROM prog_mem (
        .dout(inst_rdata),
        .clk(cpu_clk),
        .oce(1'b1),
        .ce(1'b1),
        .reset(1'b0),
        .ad(instr_addr[10:0])
    );

    memory_map_unit #(
        .STACK_BASE_ADDR(STACK_BASE_ADDR),
        .STACK_END_ADDR(STACK_END_ADDR)
    ) memory_map_i (
        .addr_in(mem_addr),
        .enable(1'b1),
        .ram_sel(ram_sel),
        .gpio_sel(gpio_sel),
        .uart_sel(uart_sel),
        .i2c_sel(i2c_sel),
        .timer_sel(timer_sel),
        .sys_sel(sys_sel),
        .stack_sel(stack_sel),
        .invalid_sel(invalid_sel)
    );

    assign ram_we      = mem_wen && ram_sel;
    assign stack_we    = mem_wen && stack_sel;
    assign gpio_we     = mem_wen && gpio_sel;
    assign gpio_re     = mem_ren && gpio_sel;
    assign uart_we     = mem_wen && uart_sel;
    assign uart_re     = mem_ren && uart_sel;
    assign i2c_we      = mem_wen && i2c_sel;
    assign i2c_re      = mem_ren && i2c_sel;
    assign sys_led_sel = sys_sel && (mem_addr[7:0] == SYS_LED_OFFSET);
    assign sys_led_we  = mem_wen && sys_led_sel;

    data_memory #(
        .MEM_SIZE(RAM_SIZE)
    ) data_mem (
        .clk(cpu_clk),
        .we(ram_we),
        .addr(mem_addr),
        .data_in(mem_wdata),
        .data_out(ram_rdata)
    );

    data_memory #(
        .MEM_SIZE(STACK_SIZE)
    ) stack_mem (
        .clk(cpu_clk),
        .we(stack_we),
        .addr(mem_addr),
        .data_in(mem_wdata),
        .data_out(stack_rdata)
    );

    gpio_peripheral #(
        .GPIO_WIDTH(GPIO_WIDTH),
        .PWM_DUTY_WIDTH(PWM_DUTY_WIDTH)
    ) gpio_mmio (
        .cpu_clk(cpu_clk),
        .pwm_clk(pwm_clk),
        .rst_n(rst_n),
        .sel(gpio_sel),
        .we(gpio_we),
        .re(gpio_re),
        .offset(mem_addr[7:0]),
        .wdata(mem_wdata),
        .gpio_in(gpio_in),
        .rdata(gpio_rdata),
        .gpio_out(gpio_out),
        .gpio_oe(gpio_oe)
    );

    uart_peripheral uart_mmio (
        .cpu_clk(cpu_clk),
        .uart_clk(uart_clk),
        .rst_n(rst_n),
        .sel(uart_sel),
        .we(uart_we),
        .re(uart_re),
        .offset(mem_addr[7:0]),
        .wdata(mem_wdata),
        .uart_rx(uart_rx),
        .rdata(uart_rdata),
        .uart_tx(uart_tx)
    );

    i2c_peripheral i2c_mmio (
        .cpu_clk(cpu_clk),
        .rst_n(rst_n),
        .sel(i2c_sel),
        .we(i2c_we),
        .re(i2c_re),
        .offset(mem_addr[7:0]),
        .wdata(mem_wdata),
        .i2c_scl(i2c_scl),
        .i2c_sda(i2c_sda),
        .rdata(i2c_rdata),
        .i2c_int()
    );

    reg_cell #(.W(8)) sys_led_reg (
        .clk(cpu_clk),
        .rst_n(rst_n),
        .we(sys_led_we),
        .oe(1'b1),
        .d(mem_wdata),
        .out(sys_led_reg_out)
    );

    assign sys_rdata = sys_led_sel ? sys_led_reg_out : 8'h00;

    assign mem_rdata = ram_sel   ? ram_rdata   :
                       stack_sel ? stack_rdata :
                       gpio_sel  ? gpio_rdata  :
                       uart_sel  ? uart_rdata  :
                       i2c_sel   ? i2c_rdata   :
                       sys_sel   ? sys_rdata   :
                       8'h00;

    assign debug_led = sys_led_reg_out;

    generate
        for (gpio_idx = 0; gpio_idx < GPIO_WIDTH; gpio_idx = gpio_idx + 1) begin : gen_gpio_pads
            assign gpio[gpio_idx] = gpio_oe[gpio_idx] ? gpio_out[gpio_idx] : 1'bz;
            assign gpio_in[gpio_idx] = gpio[gpio_idx];
        end
    endgenerate

endmodule
