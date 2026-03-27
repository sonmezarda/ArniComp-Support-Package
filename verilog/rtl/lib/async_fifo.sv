module async_fifo #(
    parameter int DATA_WIDTH = 8,
    parameter int DEPTH = 16
)(
    input  logic                  wr_clk,
    input  logic                  wr_rst_n,
    input  logic                  wr_en,
    input  logic [DATA_WIDTH-1:0] wr_data,
    output logic                  wr_full,

    input  logic                  rd_clk,
    input  logic                  rd_rst_n,
    input  logic                  rd_en,
    output logic [DATA_WIDTH-1:0] rd_data,
    output logic                  rd_empty
);

    localparam int ADDR_WIDTH = (DEPTH <= 2) ? 1 : $clog2(DEPTH);
    localparam int PTR_WIDTH  = ADDR_WIDTH + 1;

    logic [DATA_WIDTH-1:0] mem [0:DEPTH-1];

    logic [PTR_WIDTH-1:0] wr_bin, wr_bin_next;
    logic [PTR_WIDTH-1:0] wr_gray, wr_gray_next;
    logic [PTR_WIDTH-1:0] wr_bin_inc;
    logic [PTR_WIDTH-1:0] wr_gray_inc;
    logic [PTR_WIDTH-1:0] rd_bin, rd_bin_next;
    logic [PTR_WIDTH-1:0] rd_gray, rd_gray_next;

    logic [PTR_WIDTH-1:0] rd_gray_sync_1_w, rd_gray_sync_2_w;
    logic [PTR_WIDTH-1:0] wr_gray_sync_1_r, wr_gray_sync_2_r;

    logic                 wr_fire;
    logic                 rd_fire;

    function automatic logic [PTR_WIDTH-1:0] bin_to_gray(input logic [PTR_WIDTH-1:0] bin);
        return (bin >> 1) ^ bin;
    endfunction

    assign wr_bin_inc   = wr_bin + {{PTR_WIDTH-1{1'b0}}, 1'b1};
    assign wr_gray_inc  = bin_to_gray(wr_bin_inc);
    assign wr_full =
        (wr_gray_inc == {~rd_gray_sync_2_w[PTR_WIDTH-1:PTR_WIDTH-2], rd_gray_sync_2_w[PTR_WIDTH-3:0]});

    assign wr_fire = wr_en && !wr_full;
    assign rd_fire = rd_en && !rd_empty;

    assign wr_bin_next  = wr_bin + {{PTR_WIDTH-1{1'b0}}, wr_fire};
    assign rd_bin_next  = rd_bin + {{PTR_WIDTH-1{1'b0}}, rd_fire};
    assign wr_gray_next = bin_to_gray(wr_bin_next);
    assign rd_gray_next = bin_to_gray(rd_bin_next);

    assign rd_data = mem[rd_bin[ADDR_WIDTH-1:0]];

    assign rd_empty = (rd_gray == wr_gray_sync_2_r);

    always_ff @(posedge wr_clk or negedge wr_rst_n) begin
        if (!wr_rst_n) begin
            wr_bin <= '0;
            wr_gray <= '0;
            rd_gray_sync_1_w <= '0;
            rd_gray_sync_2_w <= '0;
        end else begin
            rd_gray_sync_1_w <= rd_gray;
            rd_gray_sync_2_w <= rd_gray_sync_1_w;

            if (wr_fire) begin
                mem[wr_bin[ADDR_WIDTH-1:0]] <= wr_data;
            end

            wr_bin <= wr_bin_next;
            wr_gray <= wr_gray_next;
        end
    end

    always_ff @(posedge rd_clk or negedge rd_rst_n) begin
        if (!rd_rst_n) begin
            rd_bin <= '0;
            rd_gray <= '0;
            wr_gray_sync_1_r <= '0;
            wr_gray_sync_2_r <= '0;
        end else begin
            wr_gray_sync_1_r <= wr_gray;
            wr_gray_sync_2_r <= wr_gray_sync_1_r;
            rd_bin <= rd_bin_next;
            rd_gray <= rd_gray_next;
        end
    end

endmodule
