module uart_peripheral(
    input  logic       cpu_clk,
    input  logic       uart_clk,
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

    logic [7:0] control_reg_q;
    logic [7:0] baud_sel_reg_q;
    logic [7:0] selected_output;
    logic [7:0] uart_status;

    logic       tx_fifo_wr_en_cpu;
    logic       tx_fifo_full_cpu;
    logic       tx_fifo_empty_uart;
    logic [7:0] tx_fifo_rdata_uart;
    logic       tx_fifo_rd_en_uart;

    logic       rx_fifo_wr_en_uart;
    logic       rx_fifo_full_uart;
    logic       rx_fifo_empty_cpu;
    logic [7:0] rx_fifo_rdata_cpu;
    logic       rx_fifo_rd_en_cpu;

    logic       uart_tx_busy_uart;
    logic       uart_tx_empty_uart;
    logic       uart_rx_busy_uart;
    logic       uart_rx_empty_uart;
    logic [7:0] uart_rx_rdata_uart;
    logic       uart_rx_read_uart;
    logic       uart_tx_write_uart;
    logic [7:0] uart_tx_wdata_uart;
    logic       uart_framing_error_pulse_uart;
    logic       uart_rx_overflow_pulse_uart;

    logic       uart_rx_busy_sync_1_cpu, uart_rx_busy_sync_2_cpu;
    logic       uart_tx_busy_sync_1_cpu, uart_tx_busy_sync_2_cpu;
    logic       uart_tx_empty_sync_1_cpu, uart_tx_empty_sync_2_cpu;

    logic       clear_rx_active_cpu;
    logic       framing_error_flag;
    logic       rx_overflow_flag;
    logic       framing_error_evt_toggle_uart;
    logic       rx_overflow_evt_toggle_uart;
    logic       framing_error_evt_sync_1_cpu, framing_error_evt_sync_2_cpu, framing_error_evt_seen_cpu;
    logic       rx_overflow_evt_sync_1_cpu, rx_overflow_evt_sync_2_cpu, rx_overflow_evt_seen_cpu;

    logic [2:0] baud_sel_sync_1_uart, baud_sel_sync_2_uart;
    logic [2:0] baud_sel_uart;

    logic       cpu_uart_en;
    logic       cpu_rx_en;
    logic       cpu_tx_en;
    logic       uart_en_sync_1_uart, uart_en_sync_2_uart;
    logic       rx_en_sync_1_uart, rx_en_sync_2_uart;
    logic       tx_en_sync_1_uart, tx_en_sync_2_uart;

    assign cpu_uart_en = control_reg_q[CTRL_UART_EN_BIT];
    assign cpu_rx_en   = control_reg_q[CTRL_RX_EN_BIT];
    assign cpu_tx_en   = control_reg_q[CTRL_TX_EN_BIT];

    assign tx_fifo_wr_en_cpu = sel && we && (offset == TX_DATA_ADDR) &&
                               cpu_uart_en && cpu_tx_en && !tx_fifo_full_cpu;

    assign rx_fifo_rd_en_cpu = ((sel && re && (offset == RX_DATA_ADDR) &&
                                cpu_uart_en && cpu_rx_en && !rx_fifo_empty_cpu) ||
                                (clear_rx_active_cpu && !rx_fifo_empty_cpu));

    assign uart_status = {
        1'b0,
        rx_overflow_flag,
        cpu_uart_en && cpu_tx_en && uart_tx_empty_sync_2_cpu,
        cpu_uart_en && cpu_tx_en && uart_tx_busy_sync_2_cpu,
        cpu_uart_en && cpu_tx_en && !tx_fifo_full_cpu,
        framing_error_flag,
        cpu_uart_en && cpu_rx_en && uart_rx_busy_sync_2_cpu,
        cpu_uart_en && cpu_rx_en && !rx_fifo_empty_cpu
    };

    always_comb begin
        selected_output = 8'h00;

        case (offset)
            RX_DATA_ADDR:       selected_output = rx_fifo_empty_cpu ? 8'h00 : rx_fifo_rdata_cpu;
            RX_VALID_ADDR:      selected_output = {7'b0, uart_status[STAT_RX_VALID_BIT]};
            RX_BUSY_ADDR:       selected_output = {7'b0, uart_status[STAT_RX_BUSY_BIT]};
            FRAMING_ERROR_ADDR: selected_output = {7'b0, uart_status[STAT_FRAMING_ERROR_BIT]};
            RX_OVERFLOW_ADDR:   selected_output = {7'b0, uart_status[STAT_RX_OVERFLOW_BIT]};

            TX_READY_ADDR:      selected_output = {7'b0, uart_status[STAT_TX_READY_BIT]};
            TX_BUSY_ADDR:       selected_output = {7'b0, uart_status[STAT_TX_BUSY_BIT]};
            TX_EMPTY_ADDR:      selected_output = {7'b0, uart_status[STAT_TX_EMPTY_BIT]};

            BAUD_SEL_ADDR:      selected_output = baud_sel_reg_q;
            STATUS_ADDR:        selected_output = uart_status;
            CONTROL_ADDR:       selected_output = control_reg_q;
            UART_EN_ADDR:       selected_output = {7'b0, control_reg_q[CTRL_UART_EN_BIT]};
            RX_EN_ADDR:         selected_output = {7'b0, control_reg_q[CTRL_RX_EN_BIT]};
            TX_EN_ADDR:         selected_output = {7'b0, control_reg_q[CTRL_TX_EN_BIT]};

            default:            selected_output = 8'h00;
        endcase

        rdata = (sel && re) ? selected_output : 8'h00;
    end

    always_ff @(posedge cpu_clk or negedge rst_n) begin
        if (!rst_n) begin
            control_reg_q <= 8'h00;
            baud_sel_reg_q <= 8'h00;
            clear_rx_active_cpu <= 1'b0;
            framing_error_flag <= 1'b0;
            rx_overflow_flag <= 1'b0;
            framing_error_evt_sync_1_cpu <= 1'b0;
            framing_error_evt_sync_2_cpu <= 1'b0;
            framing_error_evt_seen_cpu <= 1'b0;
            rx_overflow_evt_sync_1_cpu <= 1'b0;
            rx_overflow_evt_sync_2_cpu <= 1'b0;
            rx_overflow_evt_seen_cpu <= 1'b0;
            uart_rx_busy_sync_1_cpu <= 1'b0;
            uart_rx_busy_sync_2_cpu <= 1'b0;
            uart_tx_busy_sync_1_cpu <= 1'b0;
            uart_tx_busy_sync_2_cpu <= 1'b0;
            uart_tx_empty_sync_1_cpu <= 1'b0;
            uart_tx_empty_sync_2_cpu <= 1'b0;
        end else begin
            framing_error_evt_sync_1_cpu <= framing_error_evt_toggle_uart;
            framing_error_evt_sync_2_cpu <= framing_error_evt_sync_1_cpu;
            rx_overflow_evt_sync_1_cpu <= rx_overflow_evt_toggle_uart;
            rx_overflow_evt_sync_2_cpu <= rx_overflow_evt_sync_1_cpu;

            uart_rx_busy_sync_1_cpu <= uart_rx_busy_uart;
            uart_rx_busy_sync_2_cpu <= uart_rx_busy_sync_1_cpu;
            uart_tx_busy_sync_1_cpu <= uart_tx_busy_uart;
            uart_tx_busy_sync_2_cpu <= uart_tx_busy_sync_1_cpu;
            uart_tx_empty_sync_1_cpu <= uart_tx_empty_uart;
            uart_tx_empty_sync_2_cpu <= uart_tx_empty_sync_1_cpu;

            if (framing_error_evt_sync_2_cpu != framing_error_evt_seen_cpu) begin
                framing_error_evt_seen_cpu <= framing_error_evt_sync_2_cpu;
                framing_error_flag <= 1'b1;
            end

            if (rx_overflow_evt_sync_2_cpu != rx_overflow_evt_seen_cpu) begin
                rx_overflow_evt_seen_cpu <= rx_overflow_evt_sync_2_cpu;
                rx_overflow_flag <= 1'b1;
            end

            if (sel && we) begin
                case (offset)
                    BAUD_SEL_ADDR: baud_sel_reg_q <= {5'b0, wdata[2:0]};
                    CONTROL_ADDR:  control_reg_q <= wdata;
                    UART_EN_ADDR:  control_reg_q[CTRL_UART_EN_BIT] <= wdata[0];
                    RX_EN_ADDR:    control_reg_q[CTRL_RX_EN_BIT] <= wdata[0];
                    TX_EN_ADDR:    control_reg_q[CTRL_TX_EN_BIT] <= wdata[0];
                    CLEAR_RX_ADDR: if (wdata[0]) clear_rx_active_cpu <= 1'b1;
                    CLEAR_ERROR_ADDR: begin
                        if (wdata[0]) begin
                            framing_error_flag <= 1'b0;
                            rx_overflow_flag <= 1'b0;
                        end
                    end
                    default: begin
                    end
                endcase
            end

            if (clear_rx_active_cpu && rx_fifo_empty_cpu) begin
                clear_rx_active_cpu <= 1'b0;
            end
        end
    end

    always_ff @(posedge uart_clk or negedge rst_n) begin
        if (!rst_n) begin
            baud_sel_sync_1_uart <= 3'b000;
            baud_sel_sync_2_uart <= 3'b000;
            uart_en_sync_1_uart <= 1'b0;
            uart_en_sync_2_uart <= 1'b0;
            rx_en_sync_1_uart <= 1'b0;
            rx_en_sync_2_uart <= 1'b0;
            tx_en_sync_1_uart <= 1'b0;
            tx_en_sync_2_uart <= 1'b0;
            framing_error_evt_toggle_uart <= 1'b0;
            rx_overflow_evt_toggle_uart <= 1'b0;
        end else begin
            baud_sel_sync_1_uart <= baud_sel_reg_q[2:0];
            baud_sel_sync_2_uart <= baud_sel_sync_1_uart;
            uart_en_sync_1_uart <= cpu_uart_en;
            uart_en_sync_2_uart <= uart_en_sync_1_uart;
            rx_en_sync_1_uart <= cpu_rx_en;
            rx_en_sync_2_uart <= rx_en_sync_1_uart;
            tx_en_sync_1_uart <= cpu_tx_en;
            tx_en_sync_2_uart <= tx_en_sync_1_uart;

            if (uart_framing_error_pulse_uart) begin
                framing_error_evt_toggle_uart <= ~framing_error_evt_toggle_uart;
            end

            if (uart_rx_overflow_pulse_uart) begin
                rx_overflow_evt_toggle_uart <= ~rx_overflow_evt_toggle_uart;
            end
        end
    end

    assign baud_sel_uart = baud_sel_sync_2_uart;

    assign tx_fifo_rd_en_uart = uart_en_sync_2_uart &&
                                tx_en_sync_2_uart &&
                                !uart_tx_busy_uart &&
                                !tx_fifo_empty_uart;

    assign uart_tx_write_uart = tx_fifo_rd_en_uart;
    assign uart_tx_wdata_uart = tx_fifo_rdata_uart;

    assign rx_fifo_wr_en_uart = uart_en_sync_2_uart &&
                                rx_en_sync_2_uart &&
                                !uart_rx_empty_uart &&
                                !rx_fifo_full_uart;

    assign uart_rx_read_uart = uart_en_sync_2_uart &&
                               rx_en_sync_2_uart &&
                               !uart_rx_empty_uart &&
                               !rx_fifo_full_uart;

    async_fifo #(
        .DATA_WIDTH(8),
        .DEPTH(16)
    ) tx_async_fifo (
        .wr_clk(cpu_clk),
        .wr_rst_n(rst_n),
        .wr_en(tx_fifo_wr_en_cpu),
        .wr_data(wdata),
        .wr_full(tx_fifo_full_cpu),
        .rd_clk(uart_clk),
        .rd_rst_n(rst_n),
        .rd_en(tx_fifo_rd_en_uart),
        .rd_data(tx_fifo_rdata_uart),
        .rd_empty(tx_fifo_empty_uart)
    );

    async_fifo #(
        .DATA_WIDTH(8),
        .DEPTH(16)
    ) rx_async_fifo (
        .wr_clk(uart_clk),
        .wr_rst_n(rst_n),
        .wr_en(rx_fifo_wr_en_uart),
        .wr_data(uart_rx_rdata_uart),
        .wr_full(rx_fifo_full_uart),
        .rd_clk(cpu_clk),
        .rd_rst_n(rst_n),
        .rd_en(rx_fifo_rd_en_cpu),
        .rd_data(rx_fifo_rdata_cpu),
        .rd_empty(rx_fifo_empty_cpu)
    );

    uart_top #(
        .CLK_FREQ(27_000_000),
        .TX_FIFO_DEPTH(16),
        .RX_FIFO_DEPTH(16),
        .USE_TX_FIFO(1'b0),
        .USE_RX_FIFO(1'b0),
        .IDLE_STATE_BIT(1'b1),
        .STOP_BIT_VALUE(1'b1),
        .START_BIT_VALUE(1'b0)
    ) uart_module (
        .clk(uart_clk),
        .rst(~rst_n),
        .baud_sel(baud_sel_uart),
        .uart_rx(uart_rx),
        .uart_tx(uart_tx),
        .tx_wdata(uart_tx_wdata_uart),
        .tx_write(uart_tx_write_uart),
        .tx_full(),
        .tx_empty(uart_tx_empty_uart),
        .tx_busy(uart_tx_busy_uart),
        .rx_read(uart_rx_read_uart),
        .rx_rdata(uart_rx_rdata_uart),
        .rx_empty(uart_rx_empty_uart),
        .rx_full(),
        .rx_busy(uart_rx_busy_uart),
        .framing_error(),
        .rx_overflow(),
        .framing_error_pulse_out(uart_framing_error_pulse_uart),
        .rx_overflow_pulse_out(uart_rx_overflow_pulse_uart)
    );

endmodule
