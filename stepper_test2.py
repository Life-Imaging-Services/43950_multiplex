'''
checking several mmplex stepper boards concatenated via SPI
'''

import time
import board
import busio
import digitalio
import lis_circuitpython_tmc5130 as tmc

import keyboard

NUM_OF_STEPPERS = 3  # the number of concatenatede steppers

print(dir(board))

spi = board.SPI()
cs = digitalio.DigitalInOut(board.D5)


m = tmc.Motor(spi,chip_select=cs,baudrate=100000)
time.sleep(0.1)

# set motor currents
# b02: stealth chop
# b01: use internal sense resistors
m.reg(tmc.GCONF, 0b110)
m.reg(tmc.SW_MODE, 0b1000_1010_1100)
m.reg(tmc.IHOLD_IRUN, 0x01_04_00)  # IHOLDDELAY=1, IRUN=(4+1)/32 IHOLD=(0+1)/32
m.reg(tmc.AMAX, 5_000)
m.reg(tmc.DMAX, 10_000)

# b11 soft stop (vs hard stop)
# b05 latch_l_active: latch position to XLATCH upon active flank
# b02 pol_stop_l
# b00 stop_l_enable
m.reg(tmc.SW_MODE, 0b1000_0010_0101)  # for negative turns
# m.reg(tmc.SW_MODE, 0b1000_1001_1010)  # for positive turns

print(f'Status:    0b{m.status():08b}')
print(f'GCONF:     0x{m.reg(tmc.GCONF):06X}')
print(f'IHOLD_IRUN 0x{m.reg(tmc.IHOLD_IRUN):06X}')
print(f'SW_MODE    0b{m.reg(tmc.SW_MODE):012b}')
print('')

print(f'{m.status():08b}  XACTUAL {m.reg(tmc.XACTUAL)}')
print(m.moveby(int(-532_480/360*85), int(532_480/10)))
time_out = time.time() + 0.1
while m.stopped() and time.time() < time_out:
    pass
    print('waiting to start')
#while(not (m.status() & 0b00001000)):

time_out = time.time() + 10
t_print = time.time() + 0.5
while True:
    arrived = m.arrived()
    if time.time() > t_print:
        print(f'{m.status():08b}  XTARGET {m.reg(tmc.XTARGET):12d}  XACTUAL {m.reg(tmc.XACTUAL):12d}  XLATCH {(m.reg(tmc.XACTUAL)-m.reg(tmc.XLATCH)):12d}')
        t_print = time.time() + 0.5
    '''if keyboard.is_pressed(' '):
        break'''
    if arrived:
        print('arrived')
        break
    if time.time() > time_out:
        print('timeout')
        break
    if m.stopped():
        print('stopped')
        print(f'{m.status():08b}  XTARGET {m.reg(tmc.XTARGET):12d}  XACTUAL {m.reg(tmc.XACTUAL):12d}  XLATCH {(m.reg(tmc.XACTUAL)-m.reg(tmc.XLATCH)):12d}')
        m.moveby(int(532_480 / 360 * 80), int(532_480 / 10))

m.moveby(0, int(532_480/10))

print('Done')
