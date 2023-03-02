import sys
import time
import adafruit_bus_device.i2c_device as i2c_device

I2C_DEVICEID = 0x00
I2C_POWERMODE = 0x01
I2C_FREQUENCY = 0x02
I2C_SHAPE = 0x03
I2C_BOOST = 0x04
I2C_PVOLTAGE = 0x06
I2C_P1VOLTAGE = 0x06
I2C_P2VOLTAGE = 0x07
I2C_P3VOLTAGE = 0x08
I2C_P4VOLTAGE = 0x09
I2C_UPDATEVOLTAGE = 0x0A
I2C_AUDIO = 0x05

class MP6_HD:

    def __init__(self, i2c, base_addr=0x78, device_addr=None, i2c_addr=0x78):
        self.dev = i2c_device.I2CDevice(i2c, device_addr | base_addr if device_addr else i2c_addr)
        
        with self.dev as d:
            d.write(bytearray([
                I2C_POWERMODE, #Start Register 0x01
                0x01, # I2C_POWERMODE: 0x01 (enable)
                0x80, # I2C_FREQUENCY: 0x40 (100Hz)
                0x00, # I2C_SHAPE: 0x00 (sine wave)
                0x00, # I2C_BOOST: 0x00 (800KHz)
                0x00,
                0, 0, 0, 0,
                0x01
                ]))

            buf = bytearray([0x00] * 9)
            d.write_then_readinto(bytearray([I2C_POWERMODE,]), buf)
            print(buf)

    def set_amp(self, amp):
        with self.dev as d:
            d.write(bytearray([
                I2C_P4VOLTAGE, #Start Register 0x09
                amp | 0b001_00000,  # amp values ch4:  b7-5: ramp time, b4-0 amplitude
                0x01
                ]))

        self.readback(d)

    def set_freq(self, f):
        with self.dev as d:
            d.write(bytearray([
                I2C_FREQUENCY, #Start Register 0x09
                f
            ]))

        self.readback(d)

    def settings(self):
        with self.dev as d:
            d.write(bytearray([
                I2C_FREQUENCY, #Start Register 0x01
                0x60,  # I2C_FREQUENCY: 0x40 (100Hz)
                0x00,  # I2C_SHAPE: 0x00 (sine wave)
                0x00,  # I2C_BOOST: 0x00 (800KHz)
                0x00  # AUX: 0x00 (audio off)
            ]))

        self.readback(d)

    def powermode(self, en):
        with self.dev as d:
            d.write(bytearray([
                I2C_POWERMODE, #Start Register 0x01
                en
            ]))

        self.readback(d)

    def set_shape(self, val):
        # b0-1:shape  b2-5:0  b6:damp  b7:0
        with self.dev as d:
            d.write(bytearray([
                I2C_SHAPE, #Start Register 0x01
                val
            ]))

        self.readback(d)

    def readback(self, d):
        return
        try:
            with self.dev as d:
                buf = bytearray([0x00] * 9)
                d.write_then_readinto(bytearray([I2C_POWERMODE,]), buf)
                print([f'{b:02X} ' for b in buf])
        except Exception:
            print('read back failed')


'''Wire.beginTransmission(I2C_HIGHDRIVER_ADRESS);
Wire.write(I2C_POWERMODE); // Start Register 0x01
Wire.write(0x01); // Register 0x01 = 0x01 (enable)
Wire.write(nFrequencyByte); // Register 0x02 = 0x40 (100Hz)
Wire.write(0x00); // Register 0x03 = 0x00 (sine wave)
Wire.write(0x00); // Register 0x04 = 0x00 (800KHz)
Wire.write(0x00); // Register 0x05 = 0x00 (audio off)
Wire.write(0); // Register 0x06 = Amplitude1
Wire.write(0); // Register 0x07 = Amplitude2
Wire.write(0); // Register 0x08 = Amplitude3
Wire.write(0); // Register 0x09 = Amplitude4
Wire.write(0x01); // Register 0x0A = 0x01 (update)
Wire.endTransmission();
bPumpState[0] = false;
bPumpState[1] = false;
bPumpState[2] = false;
bPumpState[3] = false;
nPumpVoltageByte[0] = 0x1F;
nPumpVoltageByte[1] = 0x1F;
nPumpVoltageByte[2] = 0x1F;
nPumpVoltageByte[3] = 0x1F;'''


if __name__ == '__main__':
    print('testing mp6 driver...')

import board
import busio

max_retries = 1_000

i2c = busio.I2C(board.SCL, board.SDA, frequency=400_000)


for _ in range(max_retries):
    try:
        max = MP6_HD(i2c, i2c_addr=0x78)
        max.settings()
        break
    except OSError:
        pass

try:
    while True:
        inp = input('enter power level 0-31? ')
        print(inp)
        if inp[0] == 'f':
            a = None
            f = int(inp[1:])
            s = None
        elif inp[0] == 's':
            a = None
            f = None
            s = int(inp[1:])
        else:
            f = None
            a = int(inp)
            s = None
        for tries in range(max_retries):
            try:
                #max.powermode(0)
                #time.sleep(0.002)
                if a is not None:
                    max.set_amp(0b011_00000 | a)
                if f is not None:
                    max.set_freq(f)
                if s is not None:
                    max.set_shape(s)
                #time.sleep(0.001)
                #max.powermode(1)
            except OSError:
                time.sleep(0.01)
                pass
            else:
                break
        else:
            print('too many tries')
        print('tries: ', tries)


finally:
    print('shut down')
    while True:
        try:
            max.powermode(0)
        except (OSError, AttributeError):
            time.sleep(0.1)
        else:
            break
        sys.exit()



