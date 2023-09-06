`default_nettype none
`timescale 1ns/1ps

module tt_um_fifo_stevej (
    `ifdef GL_TEST
        .VPWR( 1'b1),
        .VGND( 1'b0),
    `endif
    input  wire [7:0] ui_in,    // Dedicated inputs - data sent to the fifo
    output wire [7:0] uo_out,   // Dedicated outputs - data sent from the fifo
    input  wire [7:0] uio_in,   // IOs: Bidirectional Input path
    output wire [7:0] uio_out,  // IOs: Bidirectional Output path
    output wire [7:0] uio_oe,   // IOs: Bidirectional Enable path (active high: 0=input, 1=output)
    /* verilator lint_off UNUSEDSIGNAL */
    input  wire       ena,      // will go high when the design is enabled
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

    // Sets the first two bits as being writable by the design
    // and the last 6 bits as writable by the user.
    assign uio_oe = 8'b0011_1111;

    fifo fifo_inst(
        .clk(clk),
        .rst_n(rst_n),
        .ui_in(ui_in),
        .uo_out(uo_out),
        .uio_in(uio_in),
        .uio_out(uio_out)
        );
endmodule
