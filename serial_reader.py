import serial
import conf

class SerialReader:

    def __init__(self, ser):
        self.buf = bytearray(b'')
        self.ser = ser
    def readlines(self, max=1):
        lines = []
        self.buf += self.ser.read()
        for _ in range(max):
            if b'\r\n' in self.buf:
                sep = b'\r\n'
            elif b'\r' in self.buf:
                sep = b'\r'
            elif b'\n' in self.buf:
                sep = b'\n'
            else:
                break
            line, self.buf = self.buf.split(sep, maxsplit=1 )
            lines.append(line.decode())
        return lines



if __name__ == "__main__":

    print('x')

    ser = serial.Serial(conf.serial_port, baudrate=115200)

    reader = SerialReader(ser)

    while True:
        for line in reader.readlines():
            try:
                print(eval(line))
            except SyntaxError:
                try:
                    print(exec(line))
                except Exception as e:
                    raise e
            except Exception as e:
                print(e)



