`timescale 1ns/1ps

module tb_control_rom;

    import control_pkg::*;

    logic [7:0] instr;
    ctrl_t ctrl;

    // DUT
    control_rom dut (
        .instr(instr),
        .ctrl(ctrl)
    );

    initial begin
        $display("Starting control_rom test");

        // birkaç adres test edelim
        instr = 8'h00;
        #1;
        $display("instr=%h ctrl=%b", instr, ctrl);

        instr = 8'h01;
        #1;
        $display("instr=%h ctrl=%b", instr, ctrl);

        instr = 8'h10;
        #1;
        $display("instr=%h ctrl=%b", instr, ctrl);

        instr = 8'h20;
        #1;
        $display("instr=%h ctrl=%b", instr, ctrl);

        // tüm ROM'u gez
        for (int i = 0; i < 16; i++) begin
            instr = i[7:0];
            #1;
            $display("ROM[%0h] = %b", instr, ctrl);
        end

        $display("Test finished");
        $finish;
    end

endmodule