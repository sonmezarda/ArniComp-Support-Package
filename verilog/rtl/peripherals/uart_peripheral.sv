module uart_peripheral(
    input  logic       clk,
    input  logic       rst_n,
    input  logic       sel,
    input  logic       we,
    input  logic       re,
    input  logic [7:0] offset,
    input  logic [7:0] wdata,
    input  logic       uart_rx,

    output logic [7:0] rdata,
    output logic       uart_tx
);
    
    /*
        UART MMIO Register Map
        Base address is assigned by the system memory map.
        The peripheral only decodes the local 8-bit page offset.

        RX register block
        0x00 - RX_DATA        (read)    Returns the current received byte.
                                        Reading this register consumes one RX entry.
        0x01 - RX_VALID       (read)    Returns 0x00 or 0x01.
                                        0x01 means RX_DATA contains a valid byte.
        0x02 - RX_BUSY        (read)    Returns 0x00 or 0x01.
                                        0x01 means the receiver is currently sampling a frame.
        0x03 - FRAMING_ERROR  (read)    Returns 0x00 or 0x01.
                                        Sticky error flag. Cleared by CLEAR_ERROR.
        0x04 - RX_OVERFLOW    (read)    Returns 0x00 or 0x01.
                                        Sticky overflow flag. Cleared by CLEAR_ERROR.

        TX register block
        0x10 - TX_DATA   (write)        Writes one byte into the TX FIFO or transmit path.
                                        Data is accepted only when TX_READY is 0x01.
        0x11 - TX_READY  (read)         Returns 0x00 or 0x01.
                                        0x01 means the transmit side can accept a new byte.
                                        This is typically the inverse of TX FIFO full.
        0x12 - TX_BUSY   (read)         Returns 0x00 or 0x01.
                                        0x01 means the transmitter is currently sending a frame.
        0x13 - TX_EMPTY  (read)         Returns 0x00 or 0x01.
                                        0x01 means the entire TX path is empty.

        Baud-rate control
        0x20 - BAUD_SEL       (read/write)
                                        Baud-rate selection register.
                                        Only wdata[2:0] is used.

        Packed status view
        0x30 - STATUS         (read)
                                        Bit[0] = RX_VALID
                                        Bit[1] = RX_BUSY
                                        Bit[2] = FRAMING_ERROR
                                        Bit[3] = TX_READY
                                        Bit[4] = TX_BUSY
                                        Bit[5] = TX_EMPTY
                                        Bit[6] = RX_OVERFLOW
                                        Bit[7] = 0

        Control register block
        0x40 - CONTROL        (read/write)   Writes the full control register.
        0x41 - UART_EN        (read/write)   Writes wdata[0] into CONTROL[0].
        0x42 - RX_EN          (read/write)   Writes wdata[0] into CONTROL[1].
        0x43 - TX_EN          (read/write)   Writes wdata[0] into CONTROL[2].

        Command register block
        0x44 - CLEAR_RX       (write)   Writing wdata[0] = 1 requests RX buffer clear.
                                        This is a command/strobe, not a persistent register bit.
        0x45 - CLEAR_ERROR    (write)   Writing wdata[0] = 1 clears sticky error flags.
                                        This is a command/strobe, not a persistent register bit.

        CONTROL register bit definitions
        CONTROL[0] = UART_EN  Global UART enable
        CONTROL[1] = RX_EN    Receiver enable
        CONTROL[2] = TX_EN    Transmitter enable
        CONTROL[7:3] = 0      Reserved
    */

    localparam logic [7:0] RX_DATA_ADDR       = 8'h00;
    localparam logic [7:0] RX_VALID_ADDR      = 8'h01;
    localparam logic [7:0] RX_BUSY_ADDR       = 8'h02;
    localparam logic [7:0] FRAMING_ERROR_ADDR = 8'h03;
    localparam logic [7:0] RX_OVERFLOW_ADDR   = 8'h04;

    localparam logic [7:0] TX_DATA_ADDR       = 8'h10;
    localparam logic [7:0] TX_READY_ADDR      = 8'h11;
    localparam logic [7:0] TX_BUSY_ADDR       = 8'h12;
    localparam logic [7:0] TX_EMPTY_ADDR      = 8'h13;

    localparam logic [7:0] BAUD_SEL_ADDR      = 8'h20;

    localparam logic [7:0] STATUS_ADDR        = 8'h30;
    localparam logic [7:0] CONTROL_ADDR       = 8'h40;
    localparam logic [7:0] UART_EN_ADDR       = 8'h41;
    localparam logic [7:0] RX_EN_ADDR         = 8'h42;
    localparam logic [7:0] TX_EN_ADDR         = 8'h43;
    localparam logic [7:0] CLEAR_RX_ADDR      = 8'h44;
    localparam logic [7:0] CLEAR_ERROR_ADDR   = 8'h45;

    localparam int STAT_RX_VALID_BIT          = 0;
    localparam int STAT_RX_BUSY_BIT           = 1;
    localparam int STAT_FRAMING_ERROR_BIT     = 2;
    localparam int STAT_TX_READY_BIT          = 3;
    localparam int STAT_TX_BUSY_BIT           = 4;
    localparam int STAT_TX_EMPTY_BIT          = 5;
    localparam int STAT_RX_OVERFLOW_BIT       = 6;

    localparam int CTRL_UART_EN_BIT           = 0;
    localparam int CTRL_RX_EN_BIT             = 1;
    localparam int CTRL_TX_EN_BIT             = 2;

    logic [7:0] selected_output;
    logic [7:0] control_reg_out;
    logic [7:0] control_reg_in;
    logic       control_reg_we;
    logic       baud_sel_reg_we;
    logic       tx_write_pulse;
    logic       clear_rx_pulse;
    logic       clear_error_pulse;
    logic       framing_error_flag;
    logic       rx_overflow_flag;
    logic       rx_clear_active;
    logic       mmio_rx_read;

    logic [7:0] uart_rx_rdata;
    logic       uart_rx_full;
    logic       uart_rx_empty;
    logic       uart_rx_busy; 
    logic       uart_rx_overflow;
    logic       uart_framing_error;
    logic       uart_tx_full;
    logic       uart_tx_empty;
    logic       uart_tx_busy;

    
    logic       uart_rx_read;
    logic       uart_tx_write;
    logic [7:0] uart_tx_wdata;
    
    logic [7:0] uart_status;
    assign uart_status = {
        1'b0,                                                       // [7]   reserved
        rx_overflow_flag,                                           // [6]   RX_OVERFLOW
        control_reg_out[CTRL_UART_EN_BIT] && control_reg_out[CTRL_TX_EN_BIT] && uart_tx_empty,  // [5] TX_EMPTY
        control_reg_out[CTRL_UART_EN_BIT] && control_reg_out[CTRL_TX_EN_BIT] && uart_tx_busy,   // [4] TX_BUSY
        control_reg_out[CTRL_UART_EN_BIT] && control_reg_out[CTRL_TX_EN_BIT] && ~uart_tx_full,  // [3] TX_READY
        framing_error_flag,                                          // [2]   FRAMING_ERROR
        control_reg_out[CTRL_UART_EN_BIT] && control_reg_out[CTRL_RX_EN_BIT] && uart_rx_busy,   // [1] RX_BUSY
        control_reg_out[CTRL_UART_EN_BIT] && control_reg_out[CTRL_RX_EN_BIT] && ~uart_rx_empty  // [0] RX_VALID
    };


    assign uart_tx_write = tx_write_pulse 
                            && control_reg_out[CTRL_UART_EN_BIT] 
                            && control_reg_out[CTRL_TX_EN_BIT];

    assign mmio_rx_read = sel && re && (offset == RX_DATA_ADDR)
                            && control_reg_out[CTRL_UART_EN_BIT]
                            && control_reg_out[CTRL_RX_EN_BIT];

    assign uart_rx_read = mmio_rx_read || (rx_clear_active && !mmio_rx_read && !uart_rx_empty);

    assign uart_tx_wdata = wdata;

    always_comb begin : output_selector
        selected_output = 8'h00;

        case (offset)
            RX_DATA_ADDR:       selected_output = uart_rx_empty ? 8'h00 : uart_rx_rdata;
            RX_VALID_ADDR:      selected_output = {7'b0, uart_status[STAT_RX_VALID_BIT]};
            RX_BUSY_ADDR:       selected_output = {7'b0, uart_status[STAT_RX_BUSY_BIT]};
            FRAMING_ERROR_ADDR: selected_output = {7'b0, uart_status[STAT_FRAMING_ERROR_BIT]};
            RX_OVERFLOW_ADDR:   selected_output = {7'b0, uart_status[STAT_RX_OVERFLOW_BIT]};

            TX_READY_ADDR:      selected_output = {7'b0, uart_status[STAT_TX_READY_BIT]};
            TX_BUSY_ADDR:       selected_output = {7'b0, uart_status[STAT_TX_BUSY_BIT]};
            TX_EMPTY_ADDR:      selected_output = {7'b0, uart_status[STAT_TX_EMPTY_BIT]};

            BAUD_SEL_ADDR:      selected_output = baud_sel_reg_out;

            STATUS_ADDR:        selected_output = uart_status;

            CONTROL_ADDR:       selected_output = control_reg_out;
            UART_EN_ADDR:       selected_output = {7'b0, control_reg_out[CTRL_UART_EN_BIT]};
            RX_EN_ADDR:         selected_output = {7'b0, control_reg_out[CTRL_RX_EN_BIT]};
            TX_EN_ADDR:         selected_output = {7'b0, control_reg_out[CTRL_TX_EN_BIT]};

            default:            selected_output = 8'h00;
        endcase


        rdata = (re && sel) ? selected_output : 8'h00;
    end

    always_comb begin : write_decoder
        control_reg_in    = control_reg_out;
        control_reg_we    = 1'b0;
        baud_sel_reg_we   = 1'b0;
        tx_write_pulse    = 1'b0;
        clear_rx_pulse    = 1'b0;
        clear_error_pulse = 1'b0;

        if (sel && we) begin
            case (offset)
                TX_DATA_ADDR: begin
                    tx_write_pulse = 1'b1;
                end

                BAUD_SEL_ADDR: begin
                    baud_sel_reg_we = 1'b1;
                end

                CONTROL_ADDR: begin
                    control_reg_we = 1'b1;
                    control_reg_in = wdata;
                end

                UART_EN_ADDR: begin
                    control_reg_we = 1'b1;
                    control_reg_in[CTRL_UART_EN_BIT] = wdata[0];
                end

                RX_EN_ADDR: begin
                    control_reg_we = 1'b1;
                    control_reg_in[CTRL_RX_EN_BIT] = wdata[0];
                end

                TX_EN_ADDR: begin
                    control_reg_we = 1'b1;
                    control_reg_in[CTRL_TX_EN_BIT] = wdata[0];
                end

                CLEAR_RX_ADDR: begin
                    clear_rx_pulse = wdata[0];
                end

                CLEAR_ERROR_ADDR: begin
                    clear_error_pulse = wdata[0];
                end

                default: begin
                    // No MMIO write action for unmapped offsets.
                end
            endcase
        end
    end

    always_ff @(posedge clk or negedge rst_n) begin : sticky_flags_and_commands
        if (!rst_n) begin
            framing_error_flag <= 1'b0;
            rx_overflow_flag   <= 1'b0;
            rx_clear_active    <= 1'b0;
        end else begin
            if (clear_error_pulse) begin
                framing_error_flag <= 1'b0;
                rx_overflow_flag   <= 1'b0;
            end else if (uart_framing_error) begin
                framing_error_flag <= 1'b1;
            end

            if (uart_rx_overflow) begin
                rx_overflow_flag <= 1'b1;
            end

            if (clear_rx_pulse) begin
                rx_clear_active <= 1'b1;
            end else if (rx_clear_active && uart_rx_empty) begin
                rx_clear_active <= 1'b0;
            end
        end
    end

    logic [7:0] baud_sel_reg_out;
    reg_cell #(.W(8)) baud_sel_reg(
        .clk(clk),
        .rst_n(rst_n),
        .we(baud_sel_reg_we),
        .oe(1'b1),
        .d({5'b0, wdata[2:0]}),
        .out(baud_sel_reg_out)
    );

    reg_cell #(.W(8)) control_reg(
        .clk(clk),
        .rst_n(rst_n),
        .we(control_reg_we),
        .oe(1'b1),
        .d(control_reg_in),
        .out(control_reg_out)
    );

    uart_top #(
        .CLK_FREQ(27_000_000),
        .TX_FIFO_DEPTH(16),
        .RX_FIFO_DEPTH(16),
        .IDLE_STATE_BIT(1'b1),
        .STOP_BIT_VALUE(1'b1),
        .START_BIT_VALUE(1'b0)
    ) uart_module(
        .clk(clk),           // System clock for UART logic and FIFOs
        .rst(~rst_n),           // Active-high reset for the UART block
        .baud_sel(baud_sel_reg_out[2:0]),      // Baud-rate selector input
        .uart_rx(uart_rx),// Physical UART receive pin
        .uart_tx(uart_tx),       // Physical.
        
        .tx_wdata(uart_tx_wdata),      // Byte to push into the TX path
        .tx_write(uart_tx_write),      // Write strobe for TX data
        .tx_full(uart_tx_full),       // TX FIFO cannot accept new data
        .tx_empty(uart_tx_empty),      // TX path is completely empty
        .tx_busy(uart_tx_busy),       // Transmitter is current.
        
        .rx_read(uart_rx_read),       // Read strobe to consume one RX byte
        .rx_rdata(uart_rx_rdata),      // Current byte at the RX FIFO output
        .rx_empty(uart_rx_empty),      // RX FIFO has no received data
        .rx_full(uart_rx_full),       // RX FIFO cannot accept more data
        .rx_busy(uart_rx_busy),       // Receiver is currentl.
        
        .framing_error(uart_framing_error), // Stop-bit/frame format error occurred
        .rx_overflow(uart_rx_overflow)    // Received data was dropped because RX FIFO was full
    );


endmodule
