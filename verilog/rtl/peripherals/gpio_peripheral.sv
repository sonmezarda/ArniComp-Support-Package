module gpio_peripheral #(
    parameter int GPIO_WIDTH = 16,
    parameter int PWM_DUTY_WIDTH = 12
)(
    input  logic                  cpu_clk,
    input  logic                  pwm_clk,
    input  logic                  rst_n,
    input  logic                  sel,
    input  logic                  we,
    input  logic                  re,
    input  logic [7:0]            offset,
    input  logic [7:0]            wdata,
    input  logic [GPIO_WIDTH-1:0] gpio_in,

    output logic [7:0]            rdata,
    output logic [GPIO_WIDTH-1:0] gpio_out,
    output logic [GPIO_WIDTH-1:0] gpio_oe
);

    localparam logic [7:0] GPIO0_IN_ADDR            = 8'h00;
    localparam logic [7:0] GPIO1_IN_ADDR            = 8'h01;
    localparam logic [7:0] GPIO0_OUT_ADDR           = 8'h02;
    localparam logic [7:0] GPIO1_OUT_ADDR           = 8'h03;
    localparam logic [7:0] GPIO0_DIR_ADDR           = 8'h04;
    localparam logic [7:0] GPIO1_DIR_ADDR           = 8'h05;
    localparam logic [7:0] GPIO0_PWM_EN_ADDR        = 8'h06;
    localparam logic [7:0] GPIO1_PWM_EN_ADDR        = 8'h07;
    localparam logic [7:0] GPIO0_PWM_PERIOD_LO_ADDR = 8'h08;
    localparam logic [7:0] GPIO0_PWM_PERIOD_MI_ADDR = 8'h09;
    localparam logic [7:0] GPIO0_PWM_PERIOD_HI_ADDR = 8'h0A;
    localparam logic [7:0] GPIO1_PWM_PERIOD_LO_ADDR = 8'h0B;
    localparam logic [7:0] GPIO1_PWM_PERIOD_MI_ADDR = 8'h0C;
    localparam logic [7:0] GPIO1_PWM_PERIOD_HI_ADDR = 8'h0D;

    localparam logic [7:0] GPIO_IN_BIT_BASE_ADDR    = 8'h10;
    localparam logic [7:0] GPIO_OUT_BIT_BASE_ADDR   = 8'h20;
    localparam logic [7:0] GPIO_DIR_BIT_BASE_ADDR   = 8'h30;
    localparam logic [7:0] GPIO_PWM_EN_BIT_BASE_ADDR = 8'h40;
    localparam logic [7:0] GPIO_PWM_DUTY_PAIR_BASE_ADDR = 8'h50;

    localparam logic [15:0] GPIO_ACTIVE_MASK = (GPIO_WIDTH == 16) ? 16'hFFFF : 16'h00FF;

    logic [15:0] gpio_in_ext;
    logic [4:0]  gpio_pwm_duty_pair_offset;
    logic [15:0] gpio_in_sync_1_q;
    logic [15:0] gpio_in_sync_2_q;

    logic [15:0] gpio_out_reg_q;
    logic [15:0] gpio_dir_reg_q;
    logic [15:0] gpio_pwm_en_reg_q;
    logic [15:0] gpio_out_sync_1_q;
    logic [15:0] gpio_out_sync_2_q;
    logic [15:0] gpio_dir_sync_1_q;
    logic [15:0] gpio_dir_sync_2_q;
    logic [15:0] gpio_pwm_en_sync_1_q;
    logic [15:0] gpio_pwm_en_sync_2_q;

    logic [23:0] gpio0_pwm_period_reg_q;
    logic [23:0] gpio1_pwm_period_reg_q;
    logic [23:0] gpio0_pwm_period_sync_1_q;
    logic [23:0] gpio0_pwm_period_sync_2_q;
    logic [23:0] gpio1_pwm_period_sync_1_q;
    logic [23:0] gpio1_pwm_period_sync_2_q;
    logic [23:0] gpio0_pwm_counter_q;
    logic [23:0] gpio1_pwm_counter_q;
    logic [7:0]  selected_output;

    logic [PWM_DUTY_WIDTH-1:0] pwm_duty_reg_q [0:15];
    logic [PWM_DUTY_WIDTH-1:0] pwm_duty_sync_1_q [0:15];
    logic [PWM_DUTY_WIDTH-1:0] pwm_duty_sync_2_q [0:15];
    logic [15:0]               pwm_wave;

    integer i;

    initial begin
        if ((GPIO_WIDTH != 8) && (GPIO_WIDTH != 16)) begin
            $error("gpio_peripheral only supports GPIO_WIDTH of 8 or 16.");
        end
        if ((PWM_DUTY_WIDTH < 8) || (PWM_DUTY_WIDTH > 12)) begin
            $error("gpio_peripheral supports PWM_DUTY_WIDTH values between 8 and 12.");
        end
    end

    always_comb begin
        gpio_in_ext = 16'h0000;
        gpio_in_ext[GPIO_WIDTH-1:0] = gpio_in;
        gpio_pwm_duty_pair_offset = offset[4:0] - GPIO_PWM_DUTY_PAIR_BASE_ADDR[4:0];
    end

    always_comb begin
        selected_output = 8'h00;

        case (offset)
            GPIO0_IN_ADDR:            selected_output = gpio_in_sync_2_q[7:0];
            GPIO1_IN_ADDR:            selected_output = gpio_in_sync_2_q[15:8];
            GPIO0_OUT_ADDR:           selected_output = gpio_out_reg_q[7:0];
            GPIO1_OUT_ADDR:           selected_output = gpio_out_reg_q[15:8];
            GPIO0_DIR_ADDR:           selected_output = gpio_dir_reg_q[7:0];
            GPIO1_DIR_ADDR:           selected_output = gpio_dir_reg_q[15:8];
            GPIO0_PWM_EN_ADDR:        selected_output = gpio_pwm_en_reg_q[7:0];
            GPIO1_PWM_EN_ADDR:        selected_output = gpio_pwm_en_reg_q[15:8];
            GPIO0_PWM_PERIOD_LO_ADDR: selected_output = gpio0_pwm_period_reg_q[7:0];
            GPIO0_PWM_PERIOD_MI_ADDR: selected_output = gpio0_pwm_period_reg_q[15:8];
            GPIO0_PWM_PERIOD_HI_ADDR: selected_output = gpio0_pwm_period_reg_q[23:16];
            GPIO1_PWM_PERIOD_LO_ADDR: selected_output = gpio1_pwm_period_reg_q[7:0];
            GPIO1_PWM_PERIOD_MI_ADDR: selected_output = gpio1_pwm_period_reg_q[15:8];
            GPIO1_PWM_PERIOD_HI_ADDR: selected_output = gpio1_pwm_period_reg_q[23:16];

            default: begin
                if ((offset >= GPIO_IN_BIT_BASE_ADDR) && (offset < (GPIO_IN_BIT_BASE_ADDR + 8'h10))) begin
                    selected_output = {7'b0, gpio_in_sync_2_q[offset[3:0]]};
                end else if ((offset >= GPIO_OUT_BIT_BASE_ADDR) && (offset < (GPIO_OUT_BIT_BASE_ADDR + 8'h10))) begin
                    selected_output = {7'b0, gpio_out_reg_q[offset[3:0]]};
                end else if ((offset >= GPIO_DIR_BIT_BASE_ADDR) && (offset < (GPIO_DIR_BIT_BASE_ADDR + 8'h10))) begin
                    selected_output = {7'b0, gpio_dir_reg_q[offset[3:0]]};
                end else if ((offset >= GPIO_PWM_EN_BIT_BASE_ADDR) && (offset < (GPIO_PWM_EN_BIT_BASE_ADDR + 8'h10))) begin
                    selected_output = {7'b0, gpio_pwm_en_reg_q[offset[3:0]]};
                end else if ((offset >= GPIO_PWM_DUTY_PAIR_BASE_ADDR) && (offset < (GPIO_PWM_DUTY_PAIR_BASE_ADDR + 8'h20))) begin
                    if (!gpio_pwm_duty_pair_offset[0]) begin
                        selected_output = pwm_duty_reg_q[gpio_pwm_duty_pair_offset[4:1]][7:0];
                    end else begin
                        selected_output = {4'b0000, pwm_duty_reg_q[gpio_pwm_duty_pair_offset[4:1]][11:8]};
                    end
                end
            end
        endcase

        rdata = (sel && re) ? selected_output : 8'h00;
    end

    always_ff @(posedge cpu_clk or negedge rst_n) begin
        if (!rst_n) begin
            gpio_in_sync_1_q <= 16'h0000;
            gpio_in_sync_2_q <= 16'h0000;
            gpio_out_reg_q <= 16'h0000;
            gpio_dir_reg_q <= 16'h0000;
            gpio_pwm_en_reg_q <= 16'h0000;
            gpio0_pwm_period_reg_q <= 24'd540;
            gpio1_pwm_period_reg_q <= 24'd540;

            for (i = 0; i < 16; i = i + 1) begin
                pwm_duty_reg_q[i] <= '0;
            end
        end else begin
            gpio_in_sync_1_q <= gpio_in_ext & GPIO_ACTIVE_MASK;
            gpio_in_sync_2_q <= gpio_in_sync_1_q;

            if (sel && we) begin
                case (offset)
                    GPIO0_OUT_ADDR:           gpio_out_reg_q[7:0] <= wdata;
                    GPIO1_OUT_ADDR:           gpio_out_reg_q[15:8] <= (GPIO_WIDTH == 16) ? wdata : 8'h00;
                    GPIO0_DIR_ADDR:           gpio_dir_reg_q[7:0] <= wdata;
                    GPIO1_DIR_ADDR:           gpio_dir_reg_q[15:8] <= (GPIO_WIDTH == 16) ? wdata : 8'h00;
                    GPIO0_PWM_EN_ADDR:        gpio_pwm_en_reg_q[7:0] <= wdata;
                    GPIO1_PWM_EN_ADDR:        gpio_pwm_en_reg_q[15:8] <= (GPIO_WIDTH == 16) ? wdata : 8'h00;
                    GPIO0_PWM_PERIOD_LO_ADDR: gpio0_pwm_period_reg_q[7:0] <= wdata;
                    GPIO0_PWM_PERIOD_MI_ADDR: gpio0_pwm_period_reg_q[15:8] <= wdata;
                    GPIO0_PWM_PERIOD_HI_ADDR: gpio0_pwm_period_reg_q[23:16] <= wdata;
                    GPIO1_PWM_PERIOD_LO_ADDR: if (GPIO_WIDTH == 16) gpio1_pwm_period_reg_q[7:0] <= wdata;
                    GPIO1_PWM_PERIOD_MI_ADDR: if (GPIO_WIDTH == 16) gpio1_pwm_period_reg_q[15:8] <= wdata;
                    GPIO1_PWM_PERIOD_HI_ADDR: if (GPIO_WIDTH == 16) gpio1_pwm_period_reg_q[23:16] <= wdata;
                    default: begin
                        if ((offset >= GPIO_OUT_BIT_BASE_ADDR) && (offset < (GPIO_OUT_BIT_BASE_ADDR + 8'h10))) begin
                            if ((GPIO_WIDTH == 16) || !offset[3]) begin
                                gpio_out_reg_q[offset[3:0]] <= wdata[0];
                            end
                        end else if ((offset >= GPIO_DIR_BIT_BASE_ADDR) && (offset < (GPIO_DIR_BIT_BASE_ADDR + 8'h10))) begin
                            if ((GPIO_WIDTH == 16) || !offset[3]) begin
                                gpio_dir_reg_q[offset[3:0]] <= wdata[0];
                            end
                        end else if ((offset >= GPIO_PWM_EN_BIT_BASE_ADDR) && (offset < (GPIO_PWM_EN_BIT_BASE_ADDR + 8'h10))) begin
                            if ((GPIO_WIDTH == 16) || !offset[3]) begin
                                gpio_pwm_en_reg_q[offset[3:0]] <= wdata[0];
                            end
                        end else if ((offset >= GPIO_PWM_DUTY_PAIR_BASE_ADDR) && (offset < (GPIO_PWM_DUTY_PAIR_BASE_ADDR + 8'h20))) begin
                            if ((GPIO_WIDTH == 16) || !gpio_pwm_duty_pair_offset[4]) begin
                                if (!gpio_pwm_duty_pair_offset[0]) begin
                                    pwm_duty_reg_q[gpio_pwm_duty_pair_offset[4:1]][7:0] <= wdata;
                                end else begin
                                    pwm_duty_reg_q[gpio_pwm_duty_pair_offset[4:1]][11:8] <= wdata[3:0];
                                end
                            end
                        end
                    end
                endcase
            end
        end
    end

    always_ff @(posedge pwm_clk or negedge rst_n) begin
        if (!rst_n) begin
            gpio_out_sync_1_q <= 16'h0000;
            gpio_out_sync_2_q <= 16'h0000;
            gpio_dir_sync_1_q <= 16'h0000;
            gpio_dir_sync_2_q <= 16'h0000;
            gpio_pwm_en_sync_1_q <= 16'h0000;
            gpio_pwm_en_sync_2_q <= 16'h0000;
            gpio0_pwm_period_sync_1_q <= 24'd540;
            gpio0_pwm_period_sync_2_q <= 24'd540;
            gpio1_pwm_period_sync_1_q <= 24'd540;
            gpio1_pwm_period_sync_2_q <= 24'd540;
            gpio0_pwm_counter_q <= 24'h000000;
            gpio1_pwm_counter_q <= 24'h000000;

            for (i = 0; i < 16; i = i + 1) begin
                pwm_duty_sync_1_q[i] <= '0;
                pwm_duty_sync_2_q[i] <= '0;
            end
        end else begin
            gpio_out_sync_1_q <= gpio_out_reg_q & GPIO_ACTIVE_MASK;
            gpio_out_sync_2_q <= gpio_out_sync_1_q;
            gpio_dir_sync_1_q <= gpio_dir_reg_q & GPIO_ACTIVE_MASK;
            gpio_dir_sync_2_q <= gpio_dir_sync_1_q;
            gpio_pwm_en_sync_1_q <= gpio_pwm_en_reg_q & GPIO_ACTIVE_MASK;
            gpio_pwm_en_sync_2_q <= gpio_pwm_en_sync_1_q;
            gpio0_pwm_period_sync_1_q <= gpio0_pwm_period_reg_q;
            gpio0_pwm_period_sync_2_q <= gpio0_pwm_period_sync_1_q;
            gpio1_pwm_period_sync_1_q <= gpio1_pwm_period_reg_q;
            gpio1_pwm_period_sync_2_q <= gpio1_pwm_period_sync_1_q;

            for (i = 0; i < 16; i = i + 1) begin
                pwm_duty_sync_1_q[i] <= pwm_duty_reg_q[i];
                pwm_duty_sync_2_q[i] <= pwm_duty_sync_1_q[i];
            end

            if (gpio0_pwm_counter_q >= gpio0_pwm_period_sync_2_q) begin
                gpio0_pwm_counter_q <= 24'h000000;
            end else begin
                gpio0_pwm_counter_q <= gpio0_pwm_counter_q + 24'd1;
            end

            if (gpio1_pwm_counter_q >= gpio1_pwm_period_sync_2_q) begin
                gpio1_pwm_counter_q <= 24'h000000;
            end else begin
                gpio1_pwm_counter_q <= gpio1_pwm_counter_q + 24'd1;
            end
        end
    end

    generate
        genvar pin_idx;
        for (pin_idx = 0; pin_idx < 16; pin_idx = pin_idx + 1) begin : gen_pwm_outputs
            logic [PWM_DUTY_WIDTH+23:0] scaled_high_count;
            logic [PWM_DUTY_WIDTH+23:0] pwm_counter_ext;
            logic [PWM_DUTY_WIDTH+23:0] period_plus_one;

            always_comb begin
                scaled_high_count = '0;
                pwm_counter_ext = '0;
                period_plus_one = '0;

                if (pin_idx < 8) begin
                    if (&pwm_duty_sync_2_q[pin_idx]) begin
                        pwm_wave[pin_idx] = 1'b1;
                    end else begin
                        pwm_counter_ext = {{PWM_DUTY_WIDTH{1'b0}}, gpio0_pwm_counter_q};
                        period_plus_one = {{PWM_DUTY_WIDTH{1'b0}}, gpio0_pwm_period_sync_2_q};
                        period_plus_one = period_plus_one + {{(PWM_DUTY_WIDTH+23){1'b0}}, 1'b1};
                        scaled_high_count = pwm_duty_sync_2_q[pin_idx] * period_plus_one;
                        pwm_wave[pin_idx] = (pwm_counter_ext < (scaled_high_count >> PWM_DUTY_WIDTH));
                    end
                end else begin
                    if (&pwm_duty_sync_2_q[pin_idx]) begin
                        pwm_wave[pin_idx] = 1'b1;
                    end else begin
                        pwm_counter_ext = {{PWM_DUTY_WIDTH{1'b0}}, gpio1_pwm_counter_q};
                        period_plus_one = {{PWM_DUTY_WIDTH{1'b0}}, gpio1_pwm_period_sync_2_q};
                        period_plus_one = period_plus_one + {{(PWM_DUTY_WIDTH+23){1'b0}}, 1'b1};
                        scaled_high_count = pwm_duty_sync_2_q[pin_idx] * period_plus_one;
                        pwm_wave[pin_idx] = (pwm_counter_ext < (scaled_high_count >> PWM_DUTY_WIDTH));
                    end
                end

                if (pin_idx >= GPIO_WIDTH) begin
                    pwm_wave[pin_idx] = 1'b0;
                end
            end
        end
    endgenerate

    generate
        genvar gpio_idx;
        for (gpio_idx = 0; gpio_idx < GPIO_WIDTH; gpio_idx = gpio_idx + 1) begin : gen_gpio_outputs
            assign gpio_oe[gpio_idx] = gpio_dir_sync_2_q[gpio_idx];
            assign gpio_out[gpio_idx] = gpio_pwm_en_sync_2_q[gpio_idx] ? pwm_wave[gpio_idx]
                                                                        : gpio_out_sync_2_q[gpio_idx];
        end
    endgenerate

endmodule
