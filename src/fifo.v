`default_nettype none
`timescale 1ns/1ps

/**
 * A 8-bit wide, fifo of depth 1<<INDEX_WIDTH.
 **/
module fifo(clk, rst_n, ui_in, uo_out, uio_in, uio_out);
parameter INDEX_WIDTH = 5;  // The depth of the buffer is a derived value from the width of the index. 1<<INDEX_WIDTH
parameter BUFFER_DEPTH = 1 << INDEX_WIDTH; // Do not override this unless you're a big brain genius.
input  wire [7:0] ui_in;    // Dedicated inputs - data sent to the fifo
output reg [7:0] uo_out;    // Dedicated outputs - data sent from the fifo
input  wire [7:0] uio_in;   // IOs: Bidirectional Input path
output reg [7:0] uio_out;  // IOs: Bidirectional Output path
input  wire       clk;      // clock
input  wire       rst_n;    // reset_n - low to reset

// the following flags are assigned as status pins on uio_out
reg empty; // uio_out[0]
reg full; // uio_out[1]
reg underflow; // ui_out[2]
reg overflow; // uio_out[3]
reg almost_empty; // uio_out[4]
reg almost_full; // uio_out[5]
wire write_enable; // uio_out[6]
wire read_request; // uio_out[7]

// internal counters for debugging
reg [31:0] buffer_writes;
reg [31:0] buffer_reads;

// TODO: implement
assign almost_full = 0; // TODO: implement
assign almost_empty = 0; // TODO: implement

assign write_enable = uio_out[6];
assign read_request = uio_out[7];

// these indices are sized for our depth 32 internal buffer.
// Warning: This needs to be sized to fit exactly the number of bits for BUFFER_DEPTH
reg [4:0] head_idx;
reg [4:0] tail_idx;

reg [7:0] buffer [BUFFER_DEPTH-1:0];
wire reset;
assign reset = ~rst_n;

// full means there is the minimum possible space between head tail which is 1.
assign full = tail_idx == ((head_idx - 1) % BUFFER_DEPTH); // todo: this doesn't work with wraparound
// empty means that there is the maxium possible space between head and tail which is 0.
assign empty = (head_idx == tail_idx) ? 1'b1 : 1'b0;

wire do_write;
assign do_write = write_enable && ~full;
wire overflow_attempt;
assign overflow_attempt = write_enable && full;

wire do_read;
assign do_read = read_request && ~empty;
wire underflow_attempt;
assign underflow_attempt = read_request && empty;

// Trying to read and write at the same time causes a bus conflict.
wire bus_conflict;
assign bus_conflict = write_enable && read_request;

always @(posedge clk) begin
    if (reset) begin
        // TODO: set buffer to empty.
        buffer[0] <= 8'b0000_0010; // set to 2 on reset for debugging.
        buffer_writes <= 0;
        buffer_reads <= 0;
        head_idx <= 0;
        tail_idx <= 0;
        underflow <= 0;
        overflow <= 0;
    end

    if (do_read) begin
        buffer_reads <= buffer_reads + 1;
        uo_out <= buffer[tail_idx];
        tail_idx <= ((tail_idx + 1) % BUFFER_DEPTH);
        underflow <= 0;
    end

    if (underflow_attempt) begin
            // a read attempt on an empty buffer is being attempted, set a status line.
            underflow <= 1;
    end

    if (do_write) begin
        buffer[head_idx] <= ui_in;
        tail_idx <= head_idx;
        head_idx <= ((head_idx + 1) % BUFFER_DEPTH);
        overflow <= 0;
        buffer_writes <= buffer_writes + 1;
    end

    if (overflow_attempt) begin
        // an attempt to write to a full buffer is being attempted
        overflow <= 1;
    end

    uio_out <= {1'b0, 1'b0, almost_full, almost_empty, overflow, underflow, full, empty};
end

endmodule
