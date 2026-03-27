module uart_baud_rate #(
    parameter integer CLK_FREQ = 27_000_000
)(
    input  logic       clk,
    input  logic       rst_n,
    input  logic [2:0] baud_sel, // 0:300, 1:2400, 2:9600, 3:19200, 4:38400, 5:57600, 6:115200, 7:230400
    output logic       baud_tick,
    output logic       baud_x16_tick
);
    logic [31:0] baud_rate_value;
    logic [31:0] baud_rate_x16_value;
    logic [31:0] baud_accum;
    logic [31:0] baud_x16_accum;

    always_comb begin
        case(baud_sel)
            3'd0: baud_rate_value = 32'd300;
            3'd1: baud_rate_value = 32'd2400;
            3'd2: baud_rate_value = 32'd9600;
            3'd3: baud_rate_value = 32'd19200;
            3'd4: baud_rate_value = 32'd38400;
            3'd5: baud_rate_value = 32'd57600;
            3'd6: baud_rate_value = 32'd115200;
            3'd7: baud_rate_value = 32'd230400;
            
            default: baud_rate_value = 32'd115200;
        endcase
    end

    always_comb begin
        baud_rate_x16_value = baud_rate_value << 4;
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            baud_accum    <= 32'd0;
            baud_x16_accum <= 32'd0;
            baud_tick     <= 1'b0;
            baud_x16_tick <= 1'b0;
        end else begin
            if ((baud_accum + baud_rate_value) >= CLK_FREQ) begin
                baud_accum <= baud_accum + baud_rate_value - CLK_FREQ;
                baud_tick <= 1'b1;
            end else begin
                baud_accum <= baud_accum + baud_rate_value;
                baud_tick <= 1'b0;
            end

            if ((baud_x16_accum + baud_rate_x16_value) >= CLK_FREQ) begin
                baud_x16_accum <= baud_x16_accum + baud_rate_x16_value - CLK_FREQ;
                baud_x16_tick <= 1'b1;
            end else begin
                baud_x16_accum <= baud_x16_accum + baud_rate_x16_value;
                baud_x16_tick <= 1'b0;
            end
        end
    end

endmodule
