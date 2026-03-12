module tang_nano_9k_top (
	clk,
	rst_n,
	btn_run,
	led,
	uart_tx,
	uart_rx
);
	input wire clk;
	input wire rst_n;
	input wire btn_run;
	output wire [5:0] led;
	output wire uart_tx;
	input wire uart_rx;
	localparam CLK_DIV = 135000;
	reg [17:0] clk_counter;
	reg cpu_clk;
	always @(posedge clk or negedge rst_n)
		if (!rst_n) begin
			clk_counter <= 1'sb0;
			cpu_clk <= 1'b0;
		end
		else if (clk_counter >= 134999) begin
			clk_counter <= 1'sb0;
			cpu_clk <= ~cpu_clk;
		end
		else
			clk_counter <= clk_counter + 1;
	reg [15:0] debounce_counter;
	reg rst_n_sync;
	reg rst_n_debounced;
	reg btn_run_sync;
	reg btn_run_debounced;
	always @(posedge clk) begin
		rst_n_sync <= rst_n;
		btn_run_sync <= btn_run;
	end
	always @(posedge clk)
		if (debounce_counter < 16'hffff)
			debounce_counter <= debounce_counter + 1;
		else begin
			debounce_counter <= 1'sb0;
			rst_n_debounced <= rst_n_sync;
			btn_run_debounced <= btn_run_sync;
		end
	arnicomp_top #(.PROG_MEM_FILE("rom/program.mem")) cpu(
		.clk(cpu_clk),
		.rst_n(rst_n_debounced)
	);
	assign led = ~cpu.acc_out[5:0];
endmodule
