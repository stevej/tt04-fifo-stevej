`default_nettype none
`timescale 1ns/1ps

/**
 * A 8-bit wide, fifo of depth 1<<INDEX_WIDTH.
 **/
module fifo(clk, rst_n, ui_in, uo_out, uio_in, uio_out);
parameter INDEX_WIDTH = 5;  // The depth of the buffer is a derived value from the width of the index. 1<<INDEX_WIDTH
parameter BUFFER_DEPTH = 1 << INDEX_WIDTH; // Warning: Do not override this unless you're a big brain genius.
parameter ALMOST_FULL_THRESHOLD = 28; // almost_full will be pulled high when we have fewer than this many slots free.
parameter ALMOST_EMPTY_THRESHOLD = 4; // almost_empty will be pulled high when we have more than this many slots free.
input  wire [7:0] ui_in;     // Dedicated inputs - data sent to the fifo
output reg [7:0] uo_out;     // Dedicated outputs - data sent from the fifo
input  wire [7:0] uio_in;    // IOs: Bidirectional Input path
output wire [7:0] uio_out;   // IOs: Bidirectional Output path
input  wire clk;             // clock
input  wire rst_n;           // reset_n - low to reset

// the following flags are assigned as status pins on uio_out
wire empty; // uio_out[0]
wire full; // uio_out[1]
wire underflow; // uio_out[2]
wire overflow; // uio_out[3]
wire almost_empty; // uio_out[4]
wire almost_full; // uio_out[5]
wire write_enable; // uio_out[6]
wire read_request; // uio_out[7]

// internal counters for debugging
reg [31:0] buffer_writes;
reg [31:0] buffer_reads;

assign almost_full = ALMOST_FULL_THRESHOLD < stored_items;
assign almost_empty = ALMOST_EMPTY_THRESHOLD > stored_items;

assign write_enable = uio_out[6];
assign read_request = uio_out[7];

reg [INDEX_WIDTH-1:0] head_idx;
reg [INDEX_WIDTH-1:0] tail_idx;

// The number of items in the buffer. This must be one larger than the buffer depth in order
// to hold the knowledge of how many items are being stored.
reg [INDEX_WIDTH:0] stored_items;

reg [7:0] buffer [BUFFER_DEPTH-1:0];
wire reset;
assign reset = ~rst_n;

// full means that if we try to add an item it'll overwrite the tail.
assign full = stored_items == (1<<INDEX_WIDTH) ? 1'b1 : 1'b0;
// empty means that there are no used spaces in the buffer.
assign empty = stored_items == 0 ? 1'b1 : 1'b0;

wire do_write;
assign do_write = write_enable && ~full;
assign overflow = write_enable && full;

wire do_read;
assign do_read = read_request && ~empty;
assign underflow = read_request && empty;

// Internal debug signal: Trying to read and write at the same time causes a bus conflict.
wire bus_conflict;
assign bus_conflict = write_enable && read_request;

// bits 6 & 7 are user input bits, we don't set them here.
assign uio_out = {1'b0, 1'b0, almost_full, almost_empty, overflow, underflow, full, empty};

always @(posedge clk) begin

    // The first item written is always available to be read, that makes this a First-Word Fall-Through FIFO.
    uo_out <= buffer[tail_idx];

    if (reset) begin
        // TODO: set entire buffer to empty, not just the first entry.
        buffer[0] <= 8'b0000_0000;
        buffer_writes <= 0;
        buffer_reads <= 0;
        head_idx <= 0;
        tail_idx <= 0;
        stored_items <= 0;
    end

    if (do_read) begin
        // When a read operation is indicated, go ahead and remove the item on the buffer.
        buffer_reads <= buffer_reads + 1;
        tail_idx <= (tail_idx + 1) % BUFFER_DEPTH;
        stored_items <= stored_items - 1;
    end

    if (do_write) begin
        buffer[head_idx] <= ui_in;
        head_idx <= (head_idx + 1) % BUFFER_DEPTH;
        buffer_writes <= buffer_writes + 1;
        stored_items <= stored_items + 1;
    end
end

endmodule
