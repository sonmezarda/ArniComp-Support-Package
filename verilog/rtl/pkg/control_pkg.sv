`timescale 1ns/1ps
package control_pkg;

  typedef struct packed {      
    logic        jgt;        // jump greater than
    logic        inc_mar;    // update full 16-bit MAR
    logic [1:0]  ops;        // op select OPS1 OPS0
    logic        sn;         // Set negative
    logic        ce;         // count en
    logic        jmp;        // jmp active
    logic        sc;         // set carry
       
    logic        set_lr;      // set lr = pc + 1
    logic        we;         // destination write en
    logic        accw;       // ACC write
    logic [2:0]  dsel;       // destination select
    logic        sf;         // set flags
    logic        im3_low_en; // use 3 bit low immediate

    logic        im3_high_en;// use 3 bit high immediate
    logic        inc_dec_sel;// 0 : increment, 1 : decrement
    logic        sp_sel;     // stack pointer sel
    logic [2:0]  ssel;       // source select
    logic        oe;         // output en
    logic        im5_en;     // use 5 bit immediate

  } ctrl_t;

  localparam int CTRL_W = $bits(ctrl_t);

endpackage
