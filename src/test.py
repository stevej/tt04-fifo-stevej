import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer, ClockCycles


@cocotb.test()
async def test_single_add_followed_by_single_remove(dut):
    """adds and immediately removes items for a total length larger than the buffer depth"""
    # todo: move these into first test
    write_data = [0x3F, 0x06, 0x5B, 0x4F, 0x66, 0x77, 0x88]
    read_data = [0x3F, 0x06, 0x5B, 0x4F, 0x66, 0x77, 0x88]

    dut._log.info("test.py test_fifo start")
    clock = Clock(dut.clk, 1, units="ns")
    cocotb.start_soon(clock.start())

    # reset
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 1

    # add items to fifo and read them
    for i in range(len(write_data)):
        dut.uio_out.value = 0x40  # write_enable
        dut.ui_in.value = write_data[i]  # write the item
        assert dut.uio_oe == 0xFC  # this line checks that we are seeing status bits

        await ClockCycles(dut.clk, 1)
        dut.uio_out.value = 0x80  # disable write_enable, enable read_request
        # Due to clocking, I have to wait 2 cycles before the fifo update is available for read.
        await ClockCycles(dut.clk, 2)
        assert int(dut.uo_out.value) == read_data[i]


@cocotb.test()
async def test_add_two_remove_two(dut):
    "add two items, remove two items, check that empty is true"
    clock = Clock(dut.clk, 1, units="ns")
    cocotb.start_soon(clock.start())

    # reset
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)
    assert int(dut.uio_out.value) == 17  # empty and almost_empty are set

    items = [0x01, 0x02]
    # add first item to the fifo
    dut.uio_out.value = 0x40  # write_enable
    dut.ui_in.value = items[0]  # write the item
    assert dut.uio_oe == 0xFC  # this line checks that we are seeing status bits
    await ClockCycles(dut.clk, 2)
    assert int(dut.uio_out.value) == 0

    # add second item to the fifo
    dut.uio_out.value = 0x40  # write_enable
    dut.ui_in.value = items[1]  # write the item
    await ClockCycles(dut.clk, 2)
    # write_enable is being reflected. I think because nothing in the design is driving the line change at this point.
    assert int(dut.uio_out.value) == 64

    # remove first item from the fifo
    dut.uio_out.value = 0x80  # disable write_enable, enable read_request
    # Due to clocking, I have to wait 2 cycles before the fifo update is available for read.
    await ClockCycles(dut.clk, 2)
    assert int(dut.uo_out.value) == items[0]
    assert int(dut.uio_out.value) == 0

    # remove the second item from the fifo
    dut.uio_out.value = 0x80  # disable write_enable, enable read_request
    await ClockCycles(dut.clk, 2)
    assert int(dut.uo_out.value) == items[1]

    # check that the fifo is empty
    await ClockCycles(dut.clk, 2)
    assert int(dut.uio_out.value) == 17  # empty and almost_empty are set


@cocotb.test()
async def test_underflow_on_empty_fifo(dut):
    """a write while empty results in the underflow status bit set"""
    clock = Clock(dut.clk, 1, units="ns")
    cocotb.start_soon(clock.start())

    # reset
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)
    dut._log.info("test.py reading item from empty fifo")
    # set read_request
    dut.uio_out.value = 0x80
    # ensures that we see status bits
    assert dut.uio_oe == 0xFC
    await ClockCycles(dut.clk, 1)
    # empty and underflow are set
    assert int(dut.uio_out.value) == 17  # empty and almost_empty are set


@cocotb.test()
async def test_status_bits(dut):
    """writes items until the fifo is full and then reads until the fifo is empty and checks the status bits"""
    clock = Clock(dut.clk, 1, units="ns")
    cocotb.start_soon(clock.start())

    # reset
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)

    items = [0x01, 0x02, 0x03, 0x04]

    # add items to fifo until the fifo is full, check the status bits
    # on each item added.
    assert int(dut.uio_out.value) == 17  # empty and almost empty are set
    dut.uio_out.value = 0x40  # write_enable
    dut.ui_in.value = items[0]  # write the item
    await ClockCycles(dut.clk, 1)
    assert int(dut.uio_out.value) == 64

    dut.uio_out.value = 0x40  # write_enable
    dut.ui_in.value = items[1]  # write the item
    await ClockCycles(dut.clk, 1)
    assert int(dut.uio_out.value) == 64  # empty is no longer set

    dut.uio_out.value = 0x40  # write_enable
    dut.ui_in.value = items[2]  # write the item
    await ClockCycles(dut.clk, 2)
    assert int(dut.uio_out.value) == 32  # almost_full is now set

    dut.uio_out.value = 0x40  # write_enable
    dut.ui_in.value = items[3]  # write the item
    # check that the fifo is now full.
    await ClockCycles(dut.clk, 2)
    assert int(dut.uio_out.value) == 34  # full and almost_full are set

    dut.uio_out.value = 0x80  # read_enable
    # read off item[3]
    await ClockCycles(dut.clk, 2)
    assert int(dut.uio_out.value) == 32  # almost_full is set, full is not

    # read off item[2]
    dut.uio_out.value = 0x80  # read_enable
    await ClockCycles(dut.clk, 2)
    assert int(dut.uio_out.value) == 0  # no status bits are set

    # read off item[1]
    dut.uio_out.value = 0x80  # read_enable
    await ClockCycles(dut.clk, 2)
    # only read_enable is seen here as nothing in the design is driving the wire to change.
    assert int(dut.uio_out.value) == 128

    # read off item[0], no more items left
    dut.uio_out.value = 0x80  # read_enable
    await ClockCycles(dut.clk, 2)
    assert int(dut.uio_out.value) == 17  # empty is set, almost_empty is set
