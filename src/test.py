import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer, ClockCycles

# todo: move these into first test
write_data = [0x3F, 0x06, 0x5B, 0x4F, 0x66]
read_data = [0x3F, 0x06, 0x5B, 0x4F, 0x66]


@cocotb.test()
async def test_single_add_followed_by_single_remove(dut):
    """adds and immediately removes items for a total length larger than the buffer depth"""
    dut._log.info("test.py test_fifo start")
    clock = Clock(dut.clk, 1, units="ns")
    cocotb.start_soon(clock.start())

    # reset
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

    items = [0x01, 0x02]
    # add first item to the fifo
    dut._log.info("test.py writing item: ".format(items[0]))
    dut.uio_out.value = 0x40  # write_enable
    dut.ui_in.value = items[0]  # write the item
    assert dut.uio_oe == 0xFC  # this line checks that we are seeing status bits
    await ClockCycles(dut.clk, 2)
    # add second item to the fifo
    dut._log.info("test.py writing item: ".format(items[1]))
    dut.uio_out.value = 0x40  # write_enable
    dut.ui_in.value = items[1]  # write the item
    assert dut.uio_oe == 0xFC  # this line checks that we are seeing status bits
    await ClockCycles(dut.clk, 2)
    # remove first item from the fifo
    dut.uio_out.value = 0x80  # disable write_enable, enable read_request
    # Due to clocking, I have to wait 2 cycles before the fifo update is available for read.
    await ClockCycles(dut.clk, 2)
    assert int(dut.uo_out.value) == items[0]
    # remove the second item from the fifo
    dut.uio_out.value = 0x80  # disable write_enable, enable read_request
    # Due to clocking, I have to wait 2 cycles before the fifo update is available for read.
    await ClockCycles(dut.clk, 2)
    assert int(dut.uo_out.value) == items[1]
    # check that the fifo is empty
    await ClockCycles(dut.clk, 2)
    assert int(dut.uio_out.value) == 0x1


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
    dut.uio_out.value = 0x80  # TODO: waveform doesn't show this being set
    assert dut.uio_oe == 0xFC  # this line checks that we are seeing status bits
    await ClockCycles(dut.clk, 2)
    # empty and underflow are set
    # TODO: overflow not set, waveform doesn't show read_request
    assert int(dut.uio_out.value) == 1


@cocotb.test()
async def test_overflow_on_full_fifo(dut):
    """overflow results in the overflow status bit set"""
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
    for i in range(len(items)):
        item = items[i]
        dut._log.info("test.py writing item: {item:X}".format(item=item))
        dut.uio_out.value = 0x40  # write_enable
        dut.ui_in.value = items[i]  # write the item
        await ClockCycles(dut.clk, 2)
        if i == 0:
            assert int(dut.uio_out.value) == 0
        elif i == 1:
            # as we asserted write_enable, we will see it on output.
            assert int(dut.uio_out.value) == 64
        elif i == 2:
            # The buffer is now full and overflow will occur next
            assert int(dut.uio_out.value) == 2
        elif i == 3:
            # The buffer was already full and overflow occurred
            assert int(dut.uio_out.value) == 2


# TODO
# add items to fifo until full and check overflow.
# wire up almost_full and almost_empty
# test paged writes
