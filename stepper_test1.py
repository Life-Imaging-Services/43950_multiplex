import board
import digitalio
from lis_circuitpython_tmc5130 import Motor


spi = board.SPI()
cs = digitalio.DigitalInOut(board.CE0)
m = Motor(spi,chip_select=cs,baudrate=100000)
print('Status:', m.status())
print('Stopped: ', m.stopped())
print('done')