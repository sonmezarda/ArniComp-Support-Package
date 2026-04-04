//create_clock -name clk -period 37.037 -waveform {0 18.518} [get_ports {clk}]
//create_generated_clock -name cpu_clk -source [get_ports {clk}] -divide_by 2700 [get_pins {cpu_clk_s1/Q}]
//set_clock_groups -asynchronous -group [get_clocks {clk}] -group [get_clocks {cpu_clk}]
