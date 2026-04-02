`timescale 1ns/1ps
module control_rom #(
    parameter string ROM_FILE = "rom/control_rom.mem"
)(
    input  logic [7:0] instr,
    output control_pkg::ctrl_t ctrl
);

    import control_pkg::*;
    
    logic [1:0] instr_main_sel;
    logic [2:0] arr_sel;
    logic [2:0] source_sel;
    assign instr_main_sel = instr[7:6];
    assign arr_sel = instr[5:3];
    assign source_sel = instr[2:0];
    always_comb begin
        ctrl = '0;
        ctrl.ce = 1'b1;
        case(instr_main_sel)
            2'b11: begin // LDL
                ctrl.im5_en = 1'b1;
                ctrl.we = 1'b1;
                ctrl.dsel = instr[5] == 0 
                            ? 3'b000  // Ra
                            : 3'b001; // Rd
            end 
            2'b10: begin // MOV
                ctrl.we = 1'b1;
                ctrl.oe = 1'b1;
                ctrl.dsel = instr[5:3];
                ctrl.ssel = source_sel;
            end
            2'b01: begin // arith
                ctrl.sf = 1'b1; // All alu ops sets flags
                ctrl.ssel = source_sel;
                ctrl.oe = 1'b1;
                case(arr_sel)
                    3'b000: begin // ADD
                        ctrl.ops = 2'b00; // ADD/SUB
                        ctrl.accw = 1'b1;
                    end
                    3'b001: begin // Addi
                        ctrl.ops = 2'b00;
                        ctrl.accw = 1'b1;
                        ctrl.im3_low_en = 1'b1;
                    end
                    3'b010: begin // Adc
                        ctrl.ops = 2'b00;
                        ctrl.accw = 1'b1;
                        ctrl.sc = 1'b1;
                    end
                    3'b011: begin // NOT
                        ctrl.ops = 2'b11;
                        ctrl.accw = 1'b1;
                    end
                    3'b100: begin // SUB
                        ctrl.ops = 2'b00;
                        ctrl.accw = 1'b1;
                        ctrl.sn = 1'b1;
                    end
                    3'b101: begin // SUBI
                        ctrl.ops = 2'b00;
                        ctrl.accw = 1'b1;
                        ctrl.im3_low_en = 1'b1;
                        ctrl.sn = 1'b1;
                    end
                    3'b110: begin // SBC
                        ctrl.ops = 2'b00;
                        ctrl.accw = 1'b1;
                        ctrl.sc = 1'b1;
                        ctrl.sn = 1'b1;
                    end
                    3'b111: begin // CMP
                        ctrl.ops = 2'b00;
                        ctrl.sn = 1'b1;
                    end
                endcase
            end
            2'b00: begin // others
                case(arr_sel)
                    3'b001: begin // XOR
                        ctrl.ops = 2'b10;
                        ctrl.accw = 1'b1;
                        ctrl.sf = 1'b1;
                        ctrl.ssel = source_sel;
                        ctrl.oe = 1'b1;
                    end
                    3'b010: begin // AND
                        ctrl.ops = 2'b01;
                        ctrl.accw = 1'b1;
                        ctrl.sf = 1'b1;
                        ctrl.ssel = source_sel;
                        ctrl.oe = 1'b1;
                    end
                    3'b011: begin // JMP
                        ctrl.jmp = 1'b1;
                    end
                    3'b100: begin // PUSH
                        ctrl.ssel = source_sel;
                        ctrl.oe = 1'b1;
                        ctrl.we = 1'b1;
                        ctrl.dsel = 3'b111; // write to mem
                        ctrl.inc_dec_sel = 1'b0; // increment
                        ctrl.sp_sel = 1'b1;
                    end
                    3'b101: begin // POP
                        ctrl.dsel = instr[2:0];
                        ctrl.oe = 1'b1;
                        ctrl.we = 1'b1;
                        ctrl.ssel = 3'b111; // read from mem
                        ctrl.inc_dec_sel = 1'b1; // decrement
                        ctrl.sp_sel = 1'b1;
                    end
                    3'b110: begin // LDH RA
                        ctrl.im3_high_en = 1'b1;
                        ctrl.dsel = 3'b000;
                        ctrl.we = 1'b1;
                    end
                    3'b111: begin // LDH Rd
                        ctrl.im3_high_en = 1'b1;
                        ctrl.dsel = 3'b001;
                        ctrl.we = 1'b1;
                    end
                    3'b000: begin // customs
                        case(instr[2:0])
                            3'b000: begin // NOP
                                
                            end
                            3'b001: begin // HLT
                                ctrl.ce = 1'b0;
                            end
                            3'b010: begin // INC 1 
                                ctrl.inc_dec_sel = 1'b0;
                                ctrl.inc_mar = 1'b1;
                            end
                            3'b011: begin // INC 2
                                ctrl.inc_dec_sel = 1'b0;
                                ctrl.inc_mar = 1'b1;
                            end
                            3'b100: begin // DEC 1 
                                ctrl.inc_dec_sel = 1'b1;
                                ctrl.inc_mar = 1'b1;
                            end
                            3'b101: begin // DEC 2
                                ctrl.inc_dec_sel = 1'b1;
                                ctrl.inc_mar = 1'b1;
                            end
                            3'b110: begin // JGT
                                ctrl.jmp = 1'b1;
                                ctrl.jgt = 1'b1;
                            end
                            3'b111: begin // JAL
                                ctrl.jmp = 1'b1;
                                ctrl.set_lr = 1'b1;
                            end

                        endcase
                    end
                endcase
                
            end


        endcase
        
    end
    
    /*
    // Single 24-bit ROM (256 entries)
    logic [CTRL_W-1:0] rom [0:255];

    initial begin
        `ifndef SYNTHESIS
        $display("Loading control ROM from %s", ROM_FILE);
        `endif
        $readmemh(ROM_FILE, rom);
    end

    assign ctrl = ctrl_t'(rom[instr]);
    */
endmodule