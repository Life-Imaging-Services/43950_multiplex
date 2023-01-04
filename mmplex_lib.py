def mount_chamber(slot):
    ...
# got to home position
# wait until end switch is released
# wait until end switch is pressed

def tilt_chamber(slot, angle):
    ...
    if type(angle) is bool:
        angle = 90 if angle else angle = 0

    # got to angle

def mix_chamber(slot, speed):
    ...

def switch_inlet(inlet):
    ...

def switch_outlet(outlet):
    ...

def pump(volume, rate):
    ...

class ChamberParameterList:
    ...

class Chamber:
    def __init__(self,
                 spi,
                 i2c,
                 volume,
                 parameter_list
                 ):
        self.spi = spi
        self.i2c = i2c
        self.volume = volume
        self.parameter_list = parameter_list
        self._angle = None
        self._mixspeed = None
        self._present = False
        ...

class InputValve:

    def __init__(self):
        self._position = None

class OutputValve:

    def __init__(self):
        self._position = None
        ...

class Pump:

    def __init__(self):
        ...


