import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer, ClockCycles


@cocotb.test()
async def test_single_add_followed_by_single_remove(dut):
    """adds and immediately removes items for a total length larger than the buffer depth"""
    items = [0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7]

    dut._log.info("test.py test_fifo start")
    clock = Clock(dut.clk, 1, units="ns")
    cocotb.start_soon(clock.start())

    # reset
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 1
    dut.uio_in.value = 0x0
    dut.uio_out.value = 0x0

    # add items to fifo and read them
    for i in range(len(items)):
        dut.uio_in.value = 0x40  # write_enable
        dut.ui_in.value = items[i]  # write the item
        # this line checks that we are seeing status bits
        assert int(dut.uio_oe) == 0x3F

        await ClockCycles(dut.clk, 1)
        dut.uio_in.value = 0x80  # disable write_enable, enable read_request
        # Due to clocking, I have to wait 2 cycles before the fifo update is available for read.
        await ClockCycles(dut.clk, 2)
        assert int(dut.uo_out.value) == items[i]


@cocotb.test()
async def test_add_two_remove_two(dut):
    "add two items, remove two items, check that empty is true"
    clock = Clock(dut.clk, 1, units="ns")
    cocotb.start_soon(clock.start())

    # reset
    dut.uio_in.value = 0x0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)
    assert int(dut.uio_out.value) == 17  # empty and almost_empty are set

    items = [0x01, 0x02]
    # add first item to the fifo
    dut.uio_in.value = 0x40  # write_enable
    dut.ui_in.value = items[0]  # write the item
    await ClockCycles(dut.clk, 2)
    # almost_empty is set after one write
    assert int(dut.uio_out.value) == 16

    # add second item to the fifo
    dut.uio_out.value = 0x40  # write_enable
    dut.ui_in.value = items[1]  # write the item
    await ClockCycles(dut.clk, 2)
    assert int(dut.uio_out.value) == 32

    # remove first item from the fifo
    dut.uio_in.value = 0x80  # disable write_enable, enable read_request
    # Due to clocking, I have to wait 2 cycles before the fifo update is available for read.
    await ClockCycles(dut.clk, 2)
    assert int(dut.uo_out.value) == items[0]
    # almost_empty is set
    assert int(dut.uio_out.value) == 32

    # remove the second item from the fifo
    dut.uio_in.value = 0x80  # disable write_enable, enable read_request
    await ClockCycles(dut.clk, 2)
    assert int(dut.uo_out.value) == items[1]

    # check that the fifo is empty
    dut.uio_in.value = 0x0  # we are checking the lines, not reading
    await ClockCycles(dut.clk, 2)
    # empty and almost_empty are set. also underflow? why?!
    assert int(dut.uio_out.value) == 17


@cocotb.test()
async def test_underflow_on_empty_fifo(dut):
    """a write while empty results in the underflow status bit set"""
    clock = Clock(dut.clk, 1, units="ns")
    cocotb.start_soon(clock.start())

    # reset
    dut.uio_in.value = 0x0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)
    dut._log.info("test.py reading item from empty fifo")
    # set read_request
    dut.uio_in.value = 0x80
    await ClockCycles(dut.clk, 1)
    # empty, undeflow, and almost_empty are set
    assert int(dut.uio_out.value) == 21


@cocotb.test()
async def test_status_bits(dut):
    """writes items until the fifo is full and then reads until the fifo is empty and checks the status bits"""
    clock = Clock(dut.clk, 1, units="ns")
    cocotb.start_soon(clock.start())

    # reset
    dut.uio_in.value = 0x0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)

    items = [0x01, 0x02, 0x03, 0x04]

    # add items to fifo until the fifo is full, check the status bits
    # on each item added.
    assert int(dut.uio_out.value) == 17  # empty and almost empty are set
    dut.uio_in.value = 0x40  # write_enable
    dut.ui_in.value = items[0]  # write the item
    await ClockCycles(dut.clk, 1)
    assert int(dut.uio_out.value) == 17

    dut.uio_in.value = 0x40  # write_enable
    dut.ui_in.value = items[1]  # write the item
    await ClockCycles(dut.clk, 1)
    assert int(dut.uio_out.value) == 16  # almost_empty is set

    dut.uio_in.value = 0x40  # write_enable
    dut.ui_in.value = items[2]  # write the item
    await ClockCycles(dut.clk, 2)
    assert int(dut.uio_out.value) == 32  # almost_full is now set

    dut.uio_in.value = 0x40  # write_enable
    dut.ui_in.value = items[3]  # write the item
    await ClockCycles(dut.clk, 1)
    # check that the fifo is now full.
    dut.uio_in.value = 0x0  # we are checking the lines, not reading
    await ClockCycles(dut.clk, 2)
    # full and almost_full are set.
    assert int(dut.uio_out.value) == 34

    dut.uio_in.value = 0x80  # read_enable
    # read off item[3]
    await ClockCycles(dut.clk, 2)
    assert int(dut.uio_out.value) == 32  # almost_full is set, full is not

    # read off item[2]
    dut.uio_in.value = 0x80  # read_enable
    await ClockCycles(dut.clk, 1)
    assert int(dut.uio_out.value) == 0  # no status bits are set

    # read off item[1]
    # dut.uio_in.value = 0x80  # read_enable
    await ClockCycles(dut.clk, 1)
    # almost_empty is set as there are fewer than two items left
    assert int(dut.uio_out.value) == 16

    # read off item[0], no more items left
    dut.uio_in.value = 0x80  # read_enable
    await ClockCycles(dut.clk, 1)
    assert int(dut.uio_out.value) == 21  # empty is set, almost_empty is set
