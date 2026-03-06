`timescale 1ns/1ps
package control_pkg;

  typedef struct packed {      
    logic        nc_1;   // not connected
    logic        inc;    // increment marl
    logic [1:0]  ops;    // op select OPS1 OPS0
    logic        sn;     // Set negative
    logic        ce;     // count en
    logic        jmp;    // jmp active
    logic        sc;     // set carry
    
    logic        nc_2;   // not connected
    logic        we;     // destination write en
    logic        accw;   // ACC write
    logic [2:0]  dsel;   // destination select
    logic        sf;     // set flags
    logic        im3;    // use 3 bit immediate

    logic        nc_3;
    logic        nc_4;
    logic        smsbra; // set Ra msb bit 1
    logic [2:0]  ssel;   // source select
    logic        oe;     // output en
    logic        im7;    // use 7 bit immediate

  } ctrl_t;

  localparam int CTRL_W = $bits(ctrl_t);

endpackage