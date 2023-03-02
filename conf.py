import sys
import time
import board
import busio
import digitalio
import lis_circuitpython_tmc5130 as tmc
from adafruit_extended_bus import ExtendedSPI as SPIx, ExtendedI2C as I2Cx

# define the docks numbers
dock_numbers = (1 ,2 ,3 ,4)

# define the chamber letters and piezo pump adresses
chambers_adresses = {'A' : 0x78,
                     'B' : 0x79,
                     'C' : 0x7A,
                     'D' : 0x7B,
                     }

# defines the GPIO that enables the 3.3V rail
gpio_3v_enable = digitalio.DigitalInOut(board.D14)
gpio_3v_enable.switch_to_output(True)

# defines the SPI interface for the chamber tilt motors
spi_dock = SPIx(0, 0)
cs_dock = digitalio.DigitalInOut(board.D22)

# defines the SPI interface for the pump motors
spi_pump = SPIx(1, 0)
cs_pump = digitalio.DigitalInOut(board.D26)

# defines the I2C interface for the chamber piezo pumps
i2c_chambers = I2Cx(1)

# defines the I2C interface for the flow sensor
i2c_flow_sensor = I2Cx(0)

# define the USB ports for the valves
port_selector = '/dev/ttyUSB0'
port_distributor = '/dev/ttyUSB1'

serial_port = '/dev/ttyGS0'