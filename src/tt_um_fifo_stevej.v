`default_nettype none
`timescale 1ns/1ps

module tt_um_fifo_stevej (
    input  wire [7:0] ui_in,    // Dedicated inputs - data sent to the fifo
    output wire [7:0] uo_out,   // Dedicated outputs - data sent from the fifo
    input  wire [7:0] uio_in,   // IOs: Bidirectional Input path
    output wire [7:0] uio_out,  // IOs: Bidirectional Output path
    output wire [7:0] uio_oe,   // IOs: Bidirectional Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // will go high when the design is enabled
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);
    // This creates a buffer depth of 32 because of (1<<5)
    parameter INDEX_WIDTH = 5;

    assign uio_oe = 8'b1111_1100;

    fifo #(.INDEX_WIDTH(INDEX_WIDTH)) f1(clk, rst_n, ui_in, uo_out, uio_in, uio_out);
endmodule
