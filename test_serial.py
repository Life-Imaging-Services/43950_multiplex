import serial
import time

ser = serial.Serial(port='/dev/ttyGS0', timeout=0.1,)
print(dir(ser))
while True:
    with ser:
        r = ser.read()
        r.replace(b'\r', b'\r\n')
        ser.write(r)
    #time.sleep(1)