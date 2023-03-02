import time
import serial

class ElveflowMux12:

    def __init__(self, ser):
        self.ser = ser
    def send_cmd(self, cmd, ADDR=b'1'):
        START = b'/'
        END = b'\r'
        self.ser.write(START + ADDR + cmd + END)
        print(f"{repr(cmd)[2:-1]:12}  {repr(self.ser.readline())[4:-5]}")

    def port(self, port):
        pass

    def busy(self):
        pass


if __name__ == '__main__':

    import conf

    s = ElveflowMux12(serial.Serial(conf.port_selector, baudrate=115200, timeout=1))
    d = ElveflowMux12(serial.Serial(conf.port_distributor, baudrate=115200))

    '''mux.write(b'/1ZR\r')
    print(mux.readline())
    time.sleep(5)'''
    s.send_cmd(b'O3R')
    s.send_cmd(b'Q')
    time.sleep(5)
    s.send_cmd(b'Q')
    s.send_cmd(b'O9R')
    s.send_cmd(b'Q')
    time.sleep(5)
    s.send_cmd(b'Q')
    s.send_cmd(b'?6')
    s.send_cmd(b'?17')
    time.sleep(5)
