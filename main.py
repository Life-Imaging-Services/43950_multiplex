class Pump:
    def __init__(self):
        pass

    def busy(self):
        pass

    def pump(self, volume, flow):
        pass

class Chamber:
    def __init__(self):
        self.i2c_addr = None  # i2c_address of the piezo pump
        self.volume = None  # volume in uL

    def busy(self):
        # 0 : idle, >0 : estimated number of seconds to finish, <0 : busy
        pass

    def pump(self, rate=None):
        # set the pump to the specified rate
        # return current rate
        pass

    def tilt(self):
        # tilt the chamber to the desired angle 0° = horizontal
        # return current angle
        pass

    def load(self, load=None):
        # return if chamber present (as determined by I2C ping)
        # if load >0, home the motor and tilt to 0°, display message, wait for chamber to be loaded
        # else tilt to 0°C, wait for chamber to be unloaded
        pass

class Valve:
    def __init__(self, dev):
        self.dev = dev

    def busy(self):
        pass

    def position(self):
        pass

class FlowSensor:
    pass




import board
import busio
# install adafruit_extended_bus if not present to use Linux device interfaces
from adafruit_extended_bus import ExtendedSPI as SPIx, ExtendedI2C as I2Cx

# SPI buses are used to control the TMC5130 stepper driver chips
# These chips can be daisy chained sharing one CS line and forming a shift register with 40bit x #_of_devices
# The MMPLEX_1.x uses SPI0 bus to control the chamber tilting motors and SPI1 to control the pump(s)

spi0 = SPIx(0, 0)  # use /dev/spidev0.0 SCK:GPIO#11 p23, MOSI:GPIO#10 p19, MISO:GPIO#09 p21, CS0:GPIO#08 p24 (don't use)
spi1 = SPIx(1, 0)  # use /dev/spidev1.0 SCK:GPIO#21 p40, MOSI:GPIO#20 p38, MISO:GPIO#19 p35, CS0:GPIO#18 p12 (don't use)
# for Blinka, the hardware CS lines should remain idle, use any other GPIO as CS line when instantiating bus devices

# I2C buses are used to control the chamber piezo pump drivers and read sensors like (e.g.
i2c0 = I2Cx(0)  # use /dev/i2c-0 SCL:GPIO#07 p28, SDA:GPIO#00 p27
i2c1 = I2Cx(1)  # use /dev/i2c-1 SCL:GPIO#03 p05, SDA:GPIO#02 p03

