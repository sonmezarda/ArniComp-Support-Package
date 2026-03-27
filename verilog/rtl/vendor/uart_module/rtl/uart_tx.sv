module uart_tx #(
    parameter logic IDLE_STATE_BIT  = 1'b1,
    parameter logic STOP_BIT_VALUE  = 1'b1,
    parameter logic START_BIT_VALUE = 1'b0

    )(
    input  logic       clk,
    input  logic       rst,
    input  logic       baud_tick,
    input  logic [7:0] tx_data,
    input  logic       tx_start,
    output logic       tx,
    output logic       tx_busy,
    output logic       tx_done
);

    typedef enum logic [1:0] {
        ST_IDLE,
        ST_DATA,
        ST_STOP
    } state_t;

    state_t state;

    logic [7:0] data_reg;
    logic [2:0] bit_index;
    logic       start_pending;

    always_ff @(posedge clk or posedge rst) begin
        if(rst) begin
            state     <= ST_IDLE;
            tx        <= IDLE_STATE_BIT;
            tx_busy   <= 1'b0;
            tx_done   <= 1'b0;
            data_reg  <= 8'd0;
            bit_index <= 3'd0;
            start_pending <= 1'b0;
        end else begin
            tx_done <= 1'b0;
            if (tx_start && (state == ST_IDLE) && !start_pending) begin
                data_reg <= tx_data;
                start_pending <= 1'b1;
                tx_busy <= 1'b1;
            end

            if (baud_tick) begin
                case (state)
                    ST_IDLE: begin
                        if(start_pending) begin
                            tx        <= START_BIT_VALUE;
                            bit_index <= 3'd0;
                            state     <= ST_DATA;
                            start_pending <= 1'b0;
                        end else begin
                            tx      <= IDLE_STATE_BIT;
                            tx_busy <= 1'b0;
                        end
                    end

                    ST_DATA: begin
                        tx <= data_reg[bit_index];

                        if(bit_index == 3'd7) begin
                            state <= ST_STOP;
                        end else begin
                            bit_index <= bit_index + 1'b1;
                        end
                    end

                    ST_STOP: begin
                        tx      <= STOP_BIT_VALUE;
                        tx_busy <= 1'b0;
                        tx_done <= 1'b1;
                        state   <= ST_IDLE;
                    end

                    default: begin
                        state <= ST_IDLE;
                        tx    <= IDLE_STATE_BIT;
                    end
                endcase
            end
        end
    end

endmodule
