from machine import Pin
from ttboard.mode import RPMode
from ttboard.demoboard import DemoBoard

from ttboard.boot.demoboard_detect import DemoboardDetect
DemoboardDetect.probe()

tt = DemoBoard()
# Obviously for the wrong project! We need to rewrite this for our FIFO
tt.shuttle.tt_um_rnunes2311_12bit_sar_adc.enable()
tt.mode = RPMode.ASIC_RP_CONTROL

tt.ui_in[0] = 1  # start conversion
tt.ui_in[2] = 1  # single ended

# reset
tt.reset_project(True)
tt.reset_project(False)

last_clk_out = 0
data = 0
while True:
    tt.clk.toggle()
    clk_out = tt.uo_out[6]
    # grab the data on rising or falling edge of the output clock
    if clk_out != last_clk_out:
        if clk_out:
            # print("msb", tt.uo_out[5:0])
            data = (int(tt.uo_out[0]) << 11) + (int(tt.uo_out[1]) << 10) + (int(tt.uo_out[2]) << 9) + (
                int(tt.uo_out[3]) << 8) + (int(tt.uo_out[4]) << 7) + (int(tt.uo_out[5]) << 6)
        else:
            # print("lsb", tt.uo_out[5:0])
            data += (int(tt.uo_out[0]) << 5) + (int(tt.uo_out[1]) << 4) + (int(tt.uo_out[2]) << 3) + (
                int(tt.uo_out[3]) << 2) + (int(tt.uo_out[4]) << 1) + (int(tt.uo_out[5]))
            print(data)

    last_clk_out = clk_out
