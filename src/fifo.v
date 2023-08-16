/**
 * A 8-bit wide, fifo of depth 32.
 **/
module fifo(clk, rst_n, ui_in, uo_out, uio_in, uio_out);
    input  wire [7:0] ui_in;    // Dedicated inputs - data sent to the fifo
    output wire [7:0] uo_out;    // Dedicated outputs - data sent from the fifo
    input  wire [7:0] uio_in;   // IOs: Bidirectional Input path
    output wire [7:0] uio_out;  // IOs: Bidirectional Output path
    input  wire       clk;      // clock
    input  wire       rst_n;    // reset_n - low to reset

    // the following flags are assigned as status pins on uio_out
    wire empty;
    assign empty = uio_out[0];
    wire full;
    assign full = uio_out[1];
    wire underflow;
    assign underflow = uio_out[2];
    wire overflow;
    assign overflow = uio_out[3];
    wire almost_empty;
    assign almost_empty = uio_out[4]; // TODO: unused
    wire almost_full;
    assign almost_full = uio_out[5]; // TODO: unused
    wire write_enable;
    assign write_enable = uio_out[6];
    wire read_request;
    assign read_request = uio_out[7];
    reg [31:0] buffer_writes;
    reg [31:0] buffer_reads;

reg [7:0] data_out;
assign uo_out = data_out;

reg [7:0] head_idx;
reg [7:0] tail_idx;
reg underflow_reg;
reg overflow_reg;
assign underflow = underflow_reg;
assign overflow = overflow_reg;

reg [7:0] buffer [31:0];
wire reset;
assign reset = ~rst_n;

// assign empty = head_idx == 0;
assign full = 0; // tail_idx == head_idx;
// TODO: this won't work when head_idx wraps around.
assign empty = ((head_idx - tail_idx) == 0) ? 1'b1 : 1'b0;

always @(posedge clk) begin
    if (reset) begin
        $display("design in reset");
        // TODO: set buffer to empty.
        buffer[0] <= 8'b0000_0010; // set to 2 on reset for debugging.
        buffer_writes <= 0;
        buffer_reads <= 0;
        head_idx <= 0;
        tail_idx <= 0;
        underflow_reg <= 0;
        overflow_reg <= 0;
    end
end

always @(posedge clk) begin
    if (read_request && ~empty) begin
        buffer_reads <= buffer_reads + 1;
        data_out <= buffer[tail_idx];
        tail_idx <= tail_idx + 1; // todo: mod the length in bytes. we need wraparound.
        underflow_reg <= 0;
        if (empty) begin
            // a read attempt on an empty buffer is being attempted, set a status line.
            underflow_reg <= 1;
        end
    end
end

always @(posedge clk) begin
    if (write_enable && ~full) begin
        $display("in write path with non-full fifo");
        buffer[head_idx] <= ui_in;
        tail_idx = head_idx;
        head_idx <= head_idx + 1; // todo: use mod to wraparound.
        overflow_reg <= 0;
        buffer_writes <= buffer_writes + 1;
        if (full) begin
            // an attempt to write to a full buffer is being attempted
            overflow_reg <= 1;
        end
    end
end

endmodule