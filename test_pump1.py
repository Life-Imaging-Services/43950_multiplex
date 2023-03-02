import sys
import time
import board
import busio
import digitalio
import lis_circuitpython_tmc5130 as tmc
from adafruit_extended_bus import ExtendedSPI as SPIx, ExtendedI2C as I2Cx

import conf

def pstat(m):
    print(f'{m.status():08b}  XTARGET {m.reg(tmc.XTARGET):12d}  XACTUAL {m.reg(tmc.XACTUAL):12d}  XLATCH {m.reg(tmc.XLATCH):12d}  RAMP_STAT {m.reg(tmc.RAMP_STAT):013b}')


print(dir(board))

'''spi1 = SPIx(1, 0)
spi1.deinit()
time.sleep(0.1)
cs1 = digitalio.DigitalInOut(board.D26)
mosi_1 = digitalio.DigitalInOut(board.D19)
sck_1 = digitalio.DigitalInOut(board.D20)
miso_1 = digitalio.DigitalInOut(board.D21)
cs1.switch_to_input()
mosi_1.switch_to_input()
sck_1.switch_to_input()
miso_1.switch_to_input()
input('disconnect VCC_IO to reset')
cs1.deinit()
mosi_1.deinit()
sck_1.deinit()
miso_1.deinit()'''
time.sleep(0.1)


try:
    gconf = 0b100
    p = tmc.Motor(conf.spi_pump, chip_select=conf.cs_pump, gconf=gconf, ihold_irun=0x01_10_06, num_of_motors=1, motor_num=0,
                  baudrate=250_000, phase=0, polarity=0)

    print(f'{p.status():08b}', p.reg(tmc.XACTUAL))
    print(f'{p.status():08b}', p.moveby(50000, 10000))
    while not p.arrived():
        print(f'{p.status():08b}', p.reg(tmc.XACTUAL))
        time.sleep(0.5)
    print(f'{p.status():08b}', p.reg(tmc.XACTUAL))

finally:
    conf.cs_pump.switch_to_input()
    conf.cs_pump.deinit()
    conf.spi_pump.deinit()


