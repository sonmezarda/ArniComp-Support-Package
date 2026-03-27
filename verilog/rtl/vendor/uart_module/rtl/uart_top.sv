module uart_top #(
    parameter int CLK_FREQ = 27_000_000,
    parameter int TX_FIFO_DEPTH = 16,
    parameter int RX_FIFO_DEPTH = 16,
    parameter logic IDLE_STATE_BIT  = 1'b1,
    parameter logic STOP_BIT_VALUE  = 1'b1,
    parameter logic START_BIT_VALUE = 1'b0
)(
    input  logic       clk,           // System clock for UART logic and FIFOs
    input  logic       rst,           // Active-high reset for the UART block
    input  logic [2:0] baud_sel,      // Baud-rate selector input
    input  logic       uart_rx,       // Physical UART receive pin
    output logic       uart_tx,       // Physical UART transmit pin

    // TX interface: write a byte when tx_full is low.
    input  logic [7:0] tx_wdata,      // Byte to push into the TX path
    input  logic       tx_write,      // Write strobe for TX data
    output logic       tx_full,       // TX FIFO cannot accept new data
    output logic       tx_empty,      // TX path is completely empty
    output logic       tx_busy,       // Transmitter is currently sending a frame

    // RX interface: read a byte when rx_empty is low.
    input  logic       rx_read,       // Read strobe to consume one RX byte
    output logic [7:0] rx_rdata,      // Current byte at the RX FIFO output
    output logic       rx_empty,      // RX FIFO has no received data
    output logic       rx_full,       // RX FIFO cannot accept more data
    output logic       rx_busy,       // Receiver is currently sampling a frame

    // Error flags are sticky until reset so the core can poll them safely.
    output logic       framing_error, // Stop-bit/frame format error occurred
    output logic       rx_overflow    // Received data was dropped because RX FIFO was full

);

    logic baud_tick;
    logic baud_x16_tick;

    logic [7:0] rx_data;
    logic       rx_valid;
    logic       framing_error_pulse;

    logic [7:0] tx_data;
    logic       tx_start;

    logic [7:0] tx_fifo_rdata;
    logic       tx_fifo_wr_en;
    logic       tx_fifo_rd_en;
    logic       tx_fifo_empty;

    logic       rx_fifo_wr_en;

    assign tx_fifo_wr_en = tx_write && !tx_full;
    assign rx_fifo_wr_en = rx_valid && !rx_full;
    // TX is considered empty only when both the FIFO and serializer are idle.
    assign tx_empty      = tx_fifo_empty && !tx_busy;

    uart_baud_rate #(
        .CLK_FREQ(CLK_FREQ)
    ) u_baud_rate (
        .clk(clk),
        .rst_n(~rst),
        .baud_sel(baud_sel),
        .baud_tick(baud_tick),
        .baud_x16_tick(baud_x16_tick)
    );

    uart_rx #(
        .IDLE_STATE_BIT(IDLE_STATE_BIT),
        .STOP_BIT_VALUE(STOP_BIT_VALUE),
        .START_BIT_VALUE(START_BIT_VALUE)
    ) u_uart_rx (
        .clk(clk),
        .rst(rst),
        .baud_x16_tick(baud_x16_tick),
        .rx(uart_rx),
        .rx_data(rx_data),
        .rx_valid(rx_valid),
        .rx_busy(rx_busy),
        .framing_error(framing_error_pulse)
    );

    sync_fifo #(
        .DATA_WIDTH(8),
        .DEPTH(RX_FIFO_DEPTH)
    ) u_rx_fifo (
        .clk(clk),
        .rst(rst),
        .wr_en(rx_fifo_wr_en),
        .rd_en(rx_read),
        .wr_data(rx_data),
        .rd_data(rx_rdata),
        .full(rx_full),
        .empty(rx_empty)
    );

    sync_fifo #(
        .DATA_WIDTH(8),
        .DEPTH(TX_FIFO_DEPTH)
    ) u_tx_fifo (
        .clk(clk),
        .rst(rst),
        .wr_en(tx_fifo_wr_en),
        .rd_en(tx_fifo_rd_en),
        .wr_data(tx_wdata),
        .rd_data(tx_fifo_rdata),
        .full(tx_full),
        .empty(tx_fifo_empty)
    );

    uart_tx #(
        .IDLE_STATE_BIT(IDLE_STATE_BIT),
        .STOP_BIT_VALUE(STOP_BIT_VALUE),
        .START_BIT_VALUE(START_BIT_VALUE)
    ) u_uart_tx (
        .clk(clk),
        .rst(rst),
        .baud_tick(baud_tick),
        .tx_data(tx_data),
        .tx_start(tx_start),
        .tx(uart_tx),
        .tx_busy(tx_busy),
        .tx_done()
    );

    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            tx_data      <= 8'd0;
            tx_start     <= 1'b0;
            tx_fifo_rd_en <= 1'b0;
            rx_overflow  <= 1'b0;
            framing_error <= 1'b0;
        end else begin
            tx_start      <= 1'b0;
            tx_fifo_rd_en <= 1'b0;
            if (rx_valid && rx_full) begin
                rx_overflow <= 1'b1;
            end

            if (framing_error_pulse) begin
                framing_error <= 1'b1;
            end

            if (!tx_busy && !tx_fifo_empty) begin
                tx_data      <= tx_fifo_rdata;
                tx_start     <= 1'b1;
                tx_fifo_rd_en <= 1'b1;
            end
        end
    end

endmodule
