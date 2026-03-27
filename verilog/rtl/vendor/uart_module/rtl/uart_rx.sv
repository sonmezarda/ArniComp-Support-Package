module uart_rx #(
    parameter logic IDLE_STATE_BIT  = 1'b1,
    parameter logic STOP_BIT_VALUE  = 1'b1,
    parameter logic START_BIT_VALUE = 1'b0
)(
    input logic clk,
    input logic rst,
    input logic baud_x16_tick,
    input logic rx,
    
    output logic [7:0] rx_data,
    output logic rx_valid,
    output logic rx_busy,
    output logic framing_error
);
    typedef enum logic [1:0] {
        ST_IDLE,
        ST_START,
        ST_DATA,
        ST_STOP
    } state_t;

    state_t state;

    logic [3:0] sample_count;
    logic [2:0] bit_index;
    logic [7:0] data_reg;

    logic rx_sync_0;
    logic rx_sync_1;

    // 2FF for metastability
    always_ff @(posedge clk or posedge rst ) begin : blockName
        if(rst) begin
            rx_sync_0 <= IDLE_STATE_BIT;
            rx_sync_1 <= IDLE_STATE_BIT;

        end else begin
            rx_sync_0 <= rx;
            rx_sync_1 <= rx_sync_0;
        end
    end

    always_ff @(posedge clk or posedge rst) begin
        if(rst) begin
            state         <= ST_IDLE;
            sample_count  <= 4'd0;
            bit_index     <= 3'd0;
            data_reg      <= 8'd0;
            rx_data       <= 8'd0;
            rx_valid      <= 1'b0;
            rx_busy       <= 1'b0;
            framing_error <= 1'b0;
        end else begin
            rx_valid      <= 1'b0;
            framing_error <= 1'b0;
            if(baud_x16_tick) begin
                case(state)
                    ST_IDLE: begin
                        rx_busy <= 1'b0;
                        if (rx_sync_1 == START_BIT_VALUE) begin
                            state        <= ST_START;
                            bit_index    <= 3'd0;
                            rx_busy      <= 1'b1;
                            data_reg     <= 8'd0;
                            sample_count <= 4'd0;
                        end
                    end

                    ST_START: begin
                        sample_count <= sample_count + 1'b1;
                        if(sample_count == 4'd7) begin
                            if(rx_sync_1 == START_BIT_VALUE) begin
                                // it's real start bit, start data
                                state        <= ST_DATA;
                                sample_count <= 4'd0;
                                bit_index    <= 3'd0;
                            end else begin
                                state        <= ST_IDLE;
                                rx_busy      <= 1'b0;
                                sample_count <= 4'd0;
                            end
                        end
                    end

                    ST_DATA: begin
                        sample_count <= sample_count + 1'b1;
                        if(sample_count == 4'hF) begin
                            data_reg[bit_index] <= rx_sync_1;
                            bit_index           <= bit_index + 1'b1;
                            sample_count        <= 4'd0;
                            if(bit_index == 3'b111) begin
                                state <= ST_STOP;
                            end
                        end
                    end

                    ST_STOP: begin
                        sample_count <= sample_count + 1'b1;
                        if(sample_count == 4'hF) begin
                            state        <= ST_IDLE;
                            rx_busy      <= 1'b0;
                            sample_count <= 4'd0;
                            bit_index    <= 3'd0;
                            // check stop bit
                            if(rx_sync_1 == STOP_BIT_VALUE) begin
                                rx_data       <= data_reg;
                                rx_valid      <= 1'b1;
                            end else begin
                                framing_error <= 1'b1;
                            end
                        end
                    end
                    
                    default: begin
                        state         <= ST_IDLE;
                        sample_count  <= 4'd0;
                        bit_index     <= 3'd0;
                        data_reg      <= 8'd0;
                        rx_busy       <= 1'b0;
                    end
                endcase
            end
        end
    end

endmodule
