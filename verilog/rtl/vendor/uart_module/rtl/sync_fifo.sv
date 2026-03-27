module sync_fifo #(
    parameter int DATA_WIDTH = 8,
    parameter int DEPTH = 16
)(
    input  logic                  clk,
    input  logic                  rst,
    input  logic                  wr_en,
    input  logic                  rd_en,
    input  logic [DATA_WIDTH-1:0] wr_data,
    output logic [DATA_WIDTH-1:0] rd_data,
    output logic                  full,
    output logic                  empty
);
    localparam int ADDR_WIDTH = (DEPTH <= 2) ? 1 : $clog2(DEPTH);
    localparam int COUNT_WIDTH = $clog2(DEPTH + 1);

    logic [DATA_WIDTH-1:0] mem [0:DEPTH-1];
    logic [ADDR_WIDTH-1:0] wr_ptr;
    logic [ADDR_WIDTH-1:0] rd_ptr;
    logic [COUNT_WIDTH-1:0] count;
    logic write_fire;
    logic read_fire;

    assign full = (count == DEPTH);
    assign empty = (count == 0);
    assign write_fire = wr_en && !full;
    assign read_fire = rd_en && !empty;
    assign rd_data = mem[rd_ptr];

    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            wr_ptr <= '0;
            rd_ptr <= '0;
            count  <= '0;
        end else begin
            if (write_fire) begin
                mem[wr_ptr] <= wr_data;
                if (wr_ptr == DEPTH - 1) begin
                    wr_ptr <= '0;
                end else begin
                    wr_ptr <= wr_ptr + 1'b1;
                end
            end

            if (read_fire) begin
                if (rd_ptr == DEPTH - 1) begin
                    rd_ptr <= '0;
                end else begin
                    rd_ptr <= rd_ptr + 1'b1;
                end
            end

            case ({write_fire, read_fire})
                2'b10: count <= count + 1'b1;
                2'b01: count <= count - 1'b1;
                default: count <= count;
            endcase
        end
    end

endmodule
