module i2c_peripheral(
    input  logic       cpu_clk,
    input  logic       rst_n,
    input  logic       sel,
    input  logic       we,
    input  logic       re,
    input  logic [7:0] offset,
    input  logic [7:0] wdata,
    inout  tri         i2c_scl,
    inout  tri         i2c_sda,

    output logic [7:0] rdata,
    output logic       i2c_int
);

    localparam logic [7:0] PRESCALE_LO_ADDR = 8'h00;
    localparam logic [7:0] PRESCALE_HI_ADDR = 8'h01;
    localparam logic [7:0] CONTROL_ADDR     = 8'h02;
    localparam logic [7:0] TXR_RXR_ADDR     = 8'h03;
    localparam logic [7:0] CR_SR_ADDR       = 8'h04;
    localparam logic [7:0] INT_ADDR         = 8'h05;

    typedef enum logic [2:0] {
        SEQ_IDLE,
        SEQ_WRITE_TXR,
        SEQ_WRITE_CR,
        SEQ_POLL_REQ,
        SEQ_POLL_CAPTURE
    } seq_state_t;

    localparam logic [7:0] STATUS_BUSY_DEFAULT = 8'b0100_0010;

    logic       ip_tx_en;
    logic [2:0] ip_waddr;
    logic [7:0] ip_wdata;
    logic       ip_rx_en;
    logic [2:0] ip_raddr;
    logic [7:0] ip_rdata;
    logic       cfg_write_en;
    logic       seq_tx_en;
    logic [2:0] seq_waddr;
    logic [7:0] seq_wdata;
    logic       seq_rx_en;
    logic [2:0] seq_raddr;

    logic [7:0] prescale_lo_reg_q;
    logic [7:0] prescale_hi_reg_q;
    logic [7:0] control_reg_q;
    logic [7:0] tx_shadow_q;
    logic [7:0] cmd_shadow_q;
    logic [7:0] status_cache_q;
    logic [7:0] selected_output;
    logic       cmd_pending_q;
    logic       cmd_needs_txr_q;
    logic       status_activity_seen_q;
    seq_state_t seq_state_q;

    assign cfg_write_en = sel && we && (offset <= CONTROL_ADDR);
    assign ip_tx_en = cfg_write_en || seq_tx_en;
    assign ip_waddr = cfg_write_en ? offset[2:0] : seq_waddr;
    assign ip_wdata = cfg_write_en ? wdata : seq_wdata;
    assign ip_rx_en = seq_rx_en;
    assign ip_raddr = seq_raddr;

    always_comb begin
        seq_tx_en = 1'b0;
        seq_waddr = 3'b000;
        seq_wdata = 8'h00;
        seq_rx_en = 1'b0;
        seq_raddr = CR_SR_ADDR[2:0];

        case (seq_state_q)
            SEQ_WRITE_TXR: begin
                seq_tx_en = 1'b1;
                seq_waddr = TXR_RXR_ADDR[2:0];
                seq_wdata = tx_shadow_q;
            end
            SEQ_WRITE_CR: begin
                seq_tx_en = 1'b1;
                seq_waddr = CR_SR_ADDR[2:0];
                seq_wdata = cmd_shadow_q;
            end
            SEQ_POLL_REQ: begin
                seq_rx_en = 1'b1;
            end
            default: begin
            end
        endcase
    end

    always_comb begin
        selected_output = 8'h00;

        case (offset)
            PRESCALE_LO_ADDR: selected_output = prescale_lo_reg_q;
            PRESCALE_HI_ADDR: selected_output = prescale_hi_reg_q;
            CONTROL_ADDR:     selected_output = control_reg_q;
            TXR_RXR_ADDR:     selected_output = tx_shadow_q;
            CR_SR_ADDR:       selected_output = status_cache_q;
            INT_ADDR:         selected_output = {7'b0, i2c_int};
            default:          selected_output = 8'h00;
        endcase

        rdata = (sel && re) ? selected_output : 8'h00;
    end

    always_ff @(posedge cpu_clk or negedge rst_n) begin
        if (!rst_n) begin
            prescale_lo_reg_q <= 8'h00;
            prescale_hi_reg_q <= 8'h00;
            control_reg_q <= 8'h00;
            tx_shadow_q <= 8'h00;
            cmd_shadow_q <= 8'h00;
            status_cache_q <= 8'h00;
            cmd_pending_q <= 1'b0;
            cmd_needs_txr_q <= 1'b0;
            status_activity_seen_q <= 1'b0;
            seq_state_q <= SEQ_IDLE;
        end else begin
            if (sel && we) begin
                case (offset)
                    PRESCALE_LO_ADDR: prescale_lo_reg_q <= wdata;
                    PRESCALE_HI_ADDR: prescale_hi_reg_q <= wdata;
                    CONTROL_ADDR:     control_reg_q <= wdata;
                    TXR_RXR_ADDR: tx_shadow_q <= wdata;
                    CR_SR_ADDR: begin
                        cmd_shadow_q <= wdata;
                        cmd_needs_txr_q <= wdata[4];

                        if (|wdata[7:3]) begin
                            cmd_pending_q <= 1'b1;
                            status_activity_seen_q <= 1'b0;
                            // The CPU-side MMIO bus reads combinationally, but the
                            // Gowin core exposes status through a synchronous SRAM
                            // interface. Mark the command busy here, then let the
                            // sequencer poll the live status register until the byte
                            // really finishes.
                            status_cache_q <= STATUS_BUSY_DEFAULT;
                        end else if (wdata[0]) begin
                            // Mirror a local IACK clear for software that wants the
                            // shadow IF bit to drop immediately.
                            status_cache_q[0] <= 1'b0;
                        end
                    end
                    default: begin
                    end
                endcase
            end

            case (seq_state_q)
                SEQ_IDLE: begin
                    if (cmd_pending_q) begin
                        cmd_pending_q <= 1'b0;
                        if (cmd_needs_txr_q) begin
                            seq_state_q <= SEQ_WRITE_TXR;
                        end else begin
                            seq_state_q <= SEQ_WRITE_CR;
                        end
                    end
                end
                SEQ_WRITE_TXR: begin
                    seq_state_q <= SEQ_WRITE_CR;
                end
                SEQ_WRITE_CR: begin
                    if (|cmd_shadow_q[7:3]) begin
                        seq_state_q <= SEQ_POLL_REQ;
                    end else begin
                        seq_state_q <= SEQ_IDLE;
                    end
                end
                SEQ_POLL_REQ: begin
                    seq_state_q <= SEQ_POLL_CAPTURE;
                end
                SEQ_POLL_CAPTURE: begin
                    if (ip_rdata[6] || ip_rdata[5] || ip_rdata[1] || ip_rdata[0]) begin
                        status_activity_seen_q <= 1'b1;
                    end

                    if (status_activity_seen_q ||
                        ip_rdata[6] || ip_rdata[5] || ip_rdata[1] || ip_rdata[0]) begin
                        status_cache_q <= ip_rdata;
                    end

                    if (ip_rdata[5]) begin
                        seq_state_q <= SEQ_IDLE;
                    end else if (cmd_shadow_q[6]) begin
                        if ((status_activity_seen_q ||
                             ip_rdata[6] || ip_rdata[5] || ip_rdata[1] || ip_rdata[0]) &&
                            !ip_rdata[1] && !ip_rdata[6]) begin
                            seq_state_q <= SEQ_IDLE;
                        end else begin
                            seq_state_q <= SEQ_POLL_REQ;
                        end
                    end else if ((status_activity_seen_q ||
                                   ip_rdata[6] || ip_rdata[5] || ip_rdata[1] || ip_rdata[0]) &&
                                  !ip_rdata[1]) begin
                        seq_state_q <= SEQ_IDLE;
                    end else begin
                        seq_state_q <= SEQ_POLL_REQ;
                    end
                end
                default: begin
                    seq_state_q <= SEQ_IDLE;
                end
            endcase
        end
    end

    I2C_MASTER_Top i2c_master_ip (
        .I_CLK(cpu_clk),
        .I_RESETN(rst_n),
        .I_TX_EN(ip_tx_en),
        .I_WADDR(ip_waddr),
        .I_WDATA(ip_wdata),
        .I_RX_EN(ip_rx_en),
        .I_RADDR(ip_raddr),
        .O_RDATA(ip_rdata),
        .O_IIC_INT(i2c_int),
        .SCL(i2c_scl),
        .SDA(i2c_sda)
    );

endmodule
