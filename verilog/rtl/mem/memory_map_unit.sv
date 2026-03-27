module memory_map_unit #(
    parameter logic [15:0] RAM_BASE_ADDR   = 16'h0000,
    parameter logic [15:0] RAM_END_ADDR    = 16'h07FF,
    parameter logic [15:0] GPIO_BASE_ADDR  = 16'h0800,
    parameter logic [15:0] GPIO_END_ADDR   = 16'h08FF,
    parameter logic [15:0] UART_BASE_ADDR  = 16'h0900,
    parameter logic [15:0] UART_END_ADDR   = 16'h09FF,
    parameter logic [15:0] I2C_BASE_ADDR   = 16'h0A00,
    parameter logic [15:0] I2C_END_ADDR    = 16'h0AFF,
    parameter logic [15:0] TIMER_BASE_ADDR = 16'h0B00,
    parameter logic [15:0] TIMER_END_ADDR  = 16'h0BFF,
    parameter logic [15:0] SYS_BASE_ADDR   = 16'h0C00,
    parameter logic [15:0] SYS_END_ADDR    = 16'h0CFF
)(
    input  logic [15:0] addr_in,
    input  logic        enable,

    output logic        ram_sel,
    output logic        gpio_sel,
    output logic        uart_sel,
    output logic        i2c_sel,
    output logic        timer_sel,
    output logic        sys_sel,
    output logic        invalid_sel
);

    always_comb begin
        ram_sel     = 1'b0;
        gpio_sel    = 1'b0;
        uart_sel    = 1'b0;
        i2c_sel     = 1'b0;
        timer_sel   = 1'b0;
        sys_sel     = 1'b0;
        invalid_sel = 1'b0;

        if (enable) begin
            if ((addr_in >= RAM_BASE_ADDR) && (addr_in <= RAM_END_ADDR)) begin
                ram_sel = 1'b1;
            end else if ((addr_in >= GPIO_BASE_ADDR) && (addr_in <= GPIO_END_ADDR)) begin
                gpio_sel = 1'b1;
            end else if ((addr_in >= UART_BASE_ADDR) && (addr_in <= UART_END_ADDR)) begin
                uart_sel = 1'b1;
            end else if ((addr_in >= I2C_BASE_ADDR) && (addr_in <= I2C_END_ADDR)) begin
                i2c_sel = 1'b1;
            end else if ((addr_in >= TIMER_BASE_ADDR) && (addr_in <= TIMER_END_ADDR)) begin
                timer_sel = 1'b1;
            end else if ((addr_in >= SYS_BASE_ADDR) && (addr_in <= SYS_END_ADDR)) begin
                sys_sel = 1'b1;
            end else begin
                invalid_sel = 1'b1;
            end
        end
    end

endmodule
