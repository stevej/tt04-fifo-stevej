import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer, ClockCycles

write_data = [0x3F, 0x06, 0x5B, 0x4F, 0x66]
read_data = [0x3F, 0x06, 0x5B, 0x4F, 0x66]


@cocotb.test()
async def test_fifo(dut):
    dut._log.info("test.py test_fifo start")
    clock = Clock(dut.clk, 1, units="ns")
    cocotb.start_soon(clock.start())

    # reset
    dut._log.info("reset from test harness")
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 1

    # add items to fifo and read them
    for i in range(len(write_data)):
        dut._log.info("test.py writing item: ".format(write_data[i]))
        dut.uio_out.value = 0x40  # write_enable
        dut.ui_in.value = write_data[i]  # write the item
        assert dut.uio_oe == 0xFC  # this line checks that we are seeing status bits

        await ClockCycles(dut.clk, 1)
        dut.uio_out.value = 0x80  # disable write_enable, enable read_request
        # bug: I have to wait 2 cycles after issuing a read request for the data to be on the wire.
        await ClockCycles(dut.clk, 2)
        assert int(dut.uo_out.value) == read_data[i]

#    for i in range(len(read_data)):
#        dut._log.info(f"test.py reading at index {i}")

# add items to fifo until full and check overflow.
# underflow results in a status bit
# wire up almost_full and almost_empty
# test paged writes
