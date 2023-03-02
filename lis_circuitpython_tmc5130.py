from micropython import const
import struct

DEBUG = False

PKTLEN = const(5) # packet length

GSTAT = const(0x01)  # Global status flags
GCONF = const(0x00)  # General Configuration Registers
SLAVECONF = const(0x03)  # 11..8 SENDDELAY | 7..0 UART SLAVEADDR
IOIN = const(0x04)  # Reads the state of all input pins available
    # 0 REFL_STEP | 1 REFR_DIR | 2 ENCB_DCEN_CFG4 | 3 ENCA_DCIN_CFG5 | 4 DRV_ENN_CFG6 | 5 ENC_N_DCO
    # 6 SD_MODE (1=External step and dir source) | 7 SWCOMP_IN (Shows voltage difference of SWN and SWP. Bring DIAG
        # outputs to high level with pushpull disabled to test the comparator.)
    # 31..24 VERSION: 0x11=first version of the IC. Identical numbers mean full digital compatibility.
OUTPUT = const(0x04) # NAO output for UART configuration (see manual)
X_COMPARE = const(0x05)  # Position comparison register for motion controller position strobe.
    # The Position pulse is available on output SWP_DIAG1
CHOPCONF = const(0x6C)
IHOLD_IRUN = const(0x10)  # b19..16 IHOLDDELAY | b12..0 IRUN | b4..0 IHOLD
    # IHOLDDELAY Controls the number of clock cycles for motor power down after a motion as soon as standstill is
    # detected (stst=1) and TPOWERDOWN has expired. The smooth transition avoids a motor jerk upon power down.
        # 0: instant power down
        # 1..15: Delay per current reduction step in multiple of 2^18 clocks
    # IRUN Motor run current (0=1/32…31=32/32)
    # IHOLD Standstill current (0=1/32…31=32/32)
    #In combination with StealthChop mode, setting IHOLD=0 allows to choose freewheeling
    # or coil short circuit for motor stand still.
TPOWERDOWN = const(0x11)  # 8b TPOWERDOWN sets the delay time after stand still (stst) of the motor to motor current
    # power down. Time range is about 0 to 4 seconds.
        #0: no delay, 1: minimum delay,
        #2..255: (TPOWERDOWN-1) * 2^18 tCLK
TPWMTHRS = const(0x13)  # upper velocity limit for StealthChop
RAMPMODE = const(0x20)  # 0: Position, 1: Right Turn, 2: Left Turn
XACTUAL = const(0x21)
VACTUAL = const(0x22)
VSTART = const(0x23)  # < VSTOP, Default 0
A1 = const(0x24)  # Acceleration VSTART->V1
V1 = const(0x25)  # (0: disables V1, A1, D1)
AMAX = const(0x26)  # Accelelation V1->VMAX
VMAX = const(0x27)
DMAX = const(0x28)  # Deceleration VMAX->V1
D1 = const(0x2A)  # Deceleration V1->VSTOP
VSTOP = const(0x2B)  # > VSTART, Default 10
TZEROWAIT = const(0x2C)  # 16b Defines the waiting time after ramping down to zero velocity before next movement or
    # direction inversion can start. Time range is about 0 to 2 seconds.
XTARGET = const(0x2D)  # 32b Target position for ramp mode (signed). Write a new target position to this register in order
    # to activate the ramp generator positioning in RAMPMODE=0.
    # Initialize all velocity, acceleration and deceleration parameters before.
SW_MODE = const(0x34)  # Reference Switch & StallGuard2 Event Configuration Register
RAMP_STAT = const(0x35)  # Ramp & Reference Switch Status Register
XLATCH = const(0x36)  # 32b Ramp generator latch position, latches XACTUAL upon a programmable switch event (see SW_MODE).

class Motor:
    """
    defines the TMC5130 stepper driver as an object
    """


    def __init__(self, spi, chip_select, gconf, ihold_irun, num_of_motors=1, motor_num=0, phase=1, polarity=1, baudrate=100_000):
        """
        :param spi: busio.SPI object
        :param chip_select: digitalio.DigitalInOut object
        :param baudrate:
        initializes the TMC5130 according to the datasheet example for positioning
        """
        assert 1 <= num_of_motors <= 4
        assert 0 <= motor_num <= num_of_motors-1
        self.spi = spi
        self.cs = chip_select
        if self.cs:
            self.cs.switch_to_output(True)  # initialize chipselect pin
        self.num_of_motors = num_of_motors
        self.motor_num = motor_num
        self.phase = phase
        self.polarity = polarity
        self.baudrate = baudrate
        self.Status = None
        self.Pos = None
        self.TargetPos = None
        self.outbuf = bytearray(b'\x00' * 5 * num_of_motors)
        self.inbuf = bytearray(b'\x00' * 5 * num_of_motors)
        self.error = True


        with self:
            self.reg(GSTAT)  # read GSTAT 0x01 to clear reset flag
            if self.reg(GCONF, gconf) == gconf:
                self.error = False
            else:
                raise ConnectionError('TMC5130 not connected')
                #self.error = 'TMC5130 not connected'

            self.reg(CHOPCONF, 0x000100C5)  # TOFF=3, HSTRT=4, HEND=1, TBL=2, CHM=0 (spreadCycle)
            self.reg(IHOLD_IRUN, ihold_irun)  # IHOLDDELAY=1, IRUN=4/32 of max, IHOLD=2/32 of max
            self.reg(TPWMTHRS, 0) # upper velocity for StealthChop)
            self.reg(A1, 1000)
            self.reg(V1, 5000)
            self.reg(AMAX, 5000)
            self.reg(VMAX, 20000)
            self.reg(DMAX, 5000)
            self.reg(D1, 5000)
            self.reg(VSTOP, 10)
            self.reg(RAMPMODE, 0)  # RAMPMODE 0x20 = 0 (Target position move)

    def __enter__(self):
        while self.spi.try_lock():
            pass
        while self.spi.try_lock():
            pass
        self.spi.configure(phase=self.phase, polarity=self.polarity, baudrate=self.baudrate)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cs: self.cs.value = True
        self.spi.unlock()

    def write_read(self,outbuf, inbuf):
        if self.cs: self.cs.value = False
        if DEBUG: print("DEBUG: cmd=self.spi.write_readinto(outbuf, inbuf)", " outbuf=", outbuf, " inbuf=", inbuf)
        self.spi.write_readinto(outbuf, inbuf)  # read
        if self.cs: self.cs.value = True

    def reg(self,
            regnum,
            val=None,
            signed=False
            ):
        """ returns the current value of the register
            if a value is given, it is written to the register
            self.Status is updates with the current status byte
        """

        if signed:
            f = '>Bl'  # format string for signed long
        else:
            f = '>BL'  # format string for unsigned long
        if val is None:
            #print("read", hex(regnum))
            struct.pack_into(f, self.outbuf, self.motor_num * 5, regnum, 0)
        else:
            #print("write", hex(regnum | 0x80), hex(val))
            struct.pack_into(f, self.outbuf, self.motor_num * 5, regnum | 0x80, val)
        self.write_read(self.outbuf, self.inbuf)  # read
        struct.pack_into(f, self.outbuf, self.motor_num * 5, regnum, 0)
        self.write_read(self.outbuf, self.inbuf)  # read
        self.Status, v = struct.unpack_from(f, self.inbuf, self.motor_num * 5)
        if val is None: val=0  # *******************9
        if DEBUG:print(f'{regnum:02X},    {val:8X}, {self.Status:08b}, {v:8X} {repr(v==val):7} {repr(self.outbuf):28} {repr(bytes(self.inbuf)):28}')  # *******************
        return v


    def move(self,
             relpos=None,  # [microsteps]
             abspos=None,  # [microsteps]
             speed=None    # [microstep/s]
             ):
        """ moves the motor to a relative or absolute position at the speed given
            updates self.Status with the current status byte
            returns the position before the move
        """
        # moves the motor and returns the status and the current position
        # all arguments are optional
        # if only speed [rotations/s] is given, the sign determines the direction
        # if abspos or relpos are given, the sign of the optional speed is ignored
        # if relpos is given, abspos is ignored
        self.Pos = self.reg(XACTUAL)
        if relpos is not None:
            self.reg(RAMPMODE, 0)
            if speed is not None:
                self.reg(VMAX, abs(speed))
            self.TargetPos = (self.Pos + relpos) % 2**32
            self.reg(XTARGET, self.TargetPos)
        elif abspos is not None:
            self.reg(RAMPMODE, 0)
            if speed is not None:
                self.reg(VMAX, abs(speed))
            self.TargetPos = abspos % 2**32
            self.reg(XTARGET, self.TargetPos)
        elif speed is not None:
            if speed < 0:
                self.reg(RAMPMODE, 2)
            else:
                self.reg(RAMPMODE, 1)
            self.reg(VMAX, abs(speed))
        return self.Pos

    def moveby(self,
               relpos=None,  # [microsteps]
               speed=None  # [microstep/s]
               ):
        """ moves the motor to a relative or absolute position at the speed given
            updates self.Status with the current status byte
            returns the position before the move
        """
        # moves the motor and returns the status and the current position
        # all arguments are optional
        # if only speed [rotations/s] is given, the sign determines the direction
        # if relpos is given, the sign of the optional speed is ignored
        self.Pos = self.reg(XACTUAL)
        if relpos is not None:
            self.reg(RAMPMODE, 0)
            if speed is not None:
                self.reg(VMAX, abs(speed))
            self.TargetPos = (self.Pos + relpos) % 2**32
            self.reg(XTARGET, self.TargetPos)
        elif speed is not None:
            if speed < 0:
                self.reg(RAMPMODE, 2)
            else:
                self.reg(RAMPMODE, 1)
            self.reg(VMAX, abs(speed))
        return self.Pos

    def moveto(self,
               abspos=None,  # [microsteps]
               speed=None  # [microstep/s]
               ):
        """ moves the motor to a relative or absolute position at the speed given
            updates self.Status with the current status byte
            returns the position before the move
        """
        # moves the motor and returns the status and the current position
        # all arguments are optional
        # if only speed [rotations/s] is given, the sign determines the direction
        # if abspos is given, the sign of the optional speed is ignored
        self.Pos = self.reg(XACTUAL)
        if abspos is not None:
            self.reg(RAMPMODE, 0)
            if speed is not None:
                self.reg(VMAX, abs(speed))
            self.TargetPos = abspos % 2**32
            self.reg(XTARGET, self.TargetPos)
        elif speed is not None:
            if speed < 0:
                self.reg(RAMPMODE, 2)
            else:
                self.reg(RAMPMODE, 1)
            self.reg(VMAX, abs(speed))
        return self.Pos

    def status(self):
        """ updates self.Status with the current status byte and returns it
        """
        self.reg(XACTUAL)
        return self.Status

    def switch_left(self):
        """ updates self.Status with the current status byte
            returns True if the motor is stopped
        """
        self.reg(XACTUAL)  # some read command to update the status
        return ((self.Status & 0b0100_0000) > 0)

    def switch_right(self):
        """ updates self.Status with the current status byte
            returns True if the motor is stopped
        """
        self.reg(XACTUAL)  # some read command to update the status
        return ((self.Status & 0b1000_0000) > 0)

    def stopped(self):
        """ updates self.Status with the current status byte
            returns True if the motor is stopped
        """
        self.reg(XACTUAL)  # some read command to update the status
        return ((self.Status & 0x08) > 0)

    def arrived(self):
        """ updates self.Status with the current status byte
            returns True if the motor is at the target position
        """

        self.reg(XACTUAL)  # some read command to update the status
        return ((self.Status & 0x20) > 0)

    def stalled(self):
        """ updates self.Status with the current status byte
            returns True if ???
        """

        self.reg(XACTUAL)  # some read command to update the status
        return ((self.Status & 0x04) > 0)

    def error(self):
        """ updates self.Status with the current status byte
            returns True if the error bit is set
        """

        self.reg(XACTUAL)  # some read command to update the status
        return ((self.Status & 0x02) > 0)

    def resetoccured(self):
        """ updates self.Status with the current status byte
            returns True if a reset has occurred
        """

        self.reg(XACTUAL)  # some read command to update the status
        return ((self.Status & 0x02) > 0)

class Motors:
    """
    defines several SPI-daisy-chained TMC5130 stepper drivers as an object
    set self.drives as a list of drives to be affected by future commands ([] = all drives)
    """


    def __init__(self, num, spi, chip_select, baudrate=100_000,
                 fclk=13e6, steps=200, usteps=256):
        """
        :param num: int
        :param spi: busio.SPI object
        :param chip_select: digitalio.DigitalInOut object
        :param baudrate: int, 4_000_000 max.
        :param autosend: bool, send each command automatically or accumulate for drives until send_now() is called
        """
        self.num_of_drives = num
        self.spi = spi
        self.cs = chip_select
        self.cs.switch_to_output(True)  # initialize chipselect pin
        self.baudrate = baudrate
        self._fclk = fclk  # the clock frequency, ~13Mhz when using the internal clock
        self._steps = steps
        self._usteps = usteps
        self._spr = steps * usteps  # steps/round (51_200 for 200 steps/round and 256 usteps/step)
        with self:
            pass
        self.Status = [-1] * self.num_of_drives
        self.xtarget = [None] * self.num_of_drives
        self.format = ['>BL'] * self.num_of_drives
        self.reply = [0x00] * self.num_of_drives
        self.inbuf = bytearray(b'\x00' * PKTLEN * self.num_of_drives)
        self.outbuf = bytearray(b'\x00' * PKTLEN * self.num_of_drives)
        self.outbuf2 = bytearray('\x00' * PKTLEN * self.num_of_drives)
        self.txerror = 0
        self.xactual = self.reg(XACTUAL)
        self.rampmode = self.reg(RAMPMODE)

        # initialize TMC5130
        self.reg(GSTAT)  # read GSTAT 0x01 to clear reset flag
        self.reg(GCONF, 0x00)
        self.reg(CHOPCONF, 0x000100C5)  # TOFF=3, HSTRT=4, HEND=1, TBL=2, CHM=0 (spreadCycle)
        self.reg(IHOLD_IRUN, 0x011705)  # IHOLD=0x04, IRUN=0x17 (max. current), IHOLDDELAY=6
        self.reg(TPWMTHRS, 0) # upper velocity for StealthChop)
        self.reg(A1, 1000)
        self.reg(V1, 5000)
        self.reg(AMAX, 50000)
        self.reg(VMAX, 20000)
        self.reg(DMAX, 50000)
        self.reg(D1, 5000)
        self.reg(VSTOP, 10)
        self.moveby(speed=[0,0])


    def __enter__(self):
        while self.spi.try_lock():
            pass
        while self.spi.try_lock():
            pass
        self.spi.configure(phase=1, polarity=1, baudrate=self.baudrate)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cs: self.cs.value = True
        self.spi.unlock()

    def write_read(self,outbuf, inbuf):
        self.cs.value = False
        self.spi.write_readinto(outbuf, inbuf)  # read
        self.cs.value = True

    def reg(self,
            regnum,
            val=None,
            signed=False,
           ):
        """ returns the current value of the register
            if a value is given, it is written to the register
            self.Status is updated with the current status byte
        """
        if val is None:
            val = [None] * self.num_of_drives
        elif type(val) is int:
            val = [val] * self.num_of_drives
        elif len(val) != self.num_of_drives:
            raise ValueError(f"length of ({len(val)}) does not match number of drives ({self.num_of_drives})")

        self.format = '>Bl' if signed else '>BL' # format string for signed long
        for i, v in enumerate(val):
            struct.pack_into(self.format,
                             self.outbuf,
                             i * PKTLEN,
                             regnum | (0x00 if v is None else 0x80),
                             0 if v is None else v
                             )

        if DEBUG: print('   ', end=' ')
        with self:
            self.write_read(self.outbuf, self.inbuf)  # read
            if DEBUG: ob = ' x'.join(f'{o:02X}' for o in self.outbuf); print(f"{ob:56}", end='  ')
            self.write_read(self.outbuf2, self.inbuf)  # read
        if DEBUG: ib = ' x'.join(f'{i:02X}' for i in self.inbuf); print(f"{ib:56}", end='  ')
        for drive in range(self.num_of_drives):
            if self.outbuf[drive * PKTLEN] & 0x80 :
                i = drive * PKTLEN
                self.txerror += 1 if (self.inbuf[i+1:i+5] != self.outbuf[i+1:i+5]) else 0
            self.Status[drive], self.reply[drive] = struct.unpack_from(self.format, self.inbuf, drive * PKTLEN)
            if DEBUG: print(f"{self.Status[drive]:08b}", end='  ')
            if DEBUG: print(f"{self.reply[drive]:10d}", end='  ')
        if DEBUG: print(f"txerror: {self.txerror}")
        self.outbuf[:] = bytearray('\x00' * PKTLEN * self.num_of_drives)
        return self.reply.copy()

    def move(self,
             relpos=None,  # [microsteps]
             abspos=None,  # [microsteps]
             speed=None    # [microstep/s]
             ):
        """ moves the motor to a relative or absolute position at the speed given
            updates self.Status with the current status byte
            returns the position before the move
        """
        # moves the motor and returns the status and the current position
        # all arguments are optional
        # if only speed [rotations/s] is given, the sign determines the direction
        # if abspos or relpos are given, the sign of the optional speed is ignored
        # if relpos is given, abspos is ignored
        self.xactual = self.reg(XACTUAL, signed=True)
        self.xtarget = self.reg(XTARGET, signed=True)
        self.rampmode = self.reg(RAMPMODE)

        if relpos is not None:
            if speed is not None:
                self.reg(VMAX, [abs(int(s)) if s is not None else None for s in speed])
            self.rampmode = self.reg(RAMPMODE, [0 if p is not None else None for p in relpos])
            self.xtarget = [((self.xactual[i] + int(p)) % 0x1000_0000) if p is not None else None for i, p in enumerate(relpos)]
            self.reg(XTARGET, self.xtarget)
        elif abspos is not None:
            if speed is not None:
                self.reg(VMAX, [abs(int(s)) if s is not None else None for s in speed])
            self.reg(RAMPMODE, [0 if p is not None else None for p in abspos])
            self.xtarget = [(int(p) % 0x1_0000_0000) if p is not None else None for i, p in enumerate(abspos)]
            self.reg(XTARGET, self.xtarget)
        elif speed is not None:
            self.reg(VMAX, [abs(s) if s is not None else None for s in speed])
            self.reg(RAMPMODE, [(2 if s < 0 else 1) if s is not None else None for s in speed])
        return self.xactual

    def moveby(self,
               relpos=None,  # [microsteps]
               speed=None,  # [microstep/s]
               ):
        """ moves the motor to a relative or absolute position at the speed given
            updates self.Status with the current status byte
            returns the position before the move
        """
        # moves the motor and returns the status and the current position
        # all arguments are optional
        # if only speed [rotations/s] is given, the sign determines the direction
        # if relpos is given, the sign of the optional speed is ignored
        return self.move(relpos=relpos, speed=speed)

    def moveto(self,
               abspos=None,  # [microsteps]
               speed=None  # [microstep/s]
               ):
        """ moves the motor to a relative or absolute position at the speed given
            updates self.Status with the current status byte
            returns the position before the move
        """
        # moves the motor and returns the status and the current position
        # all arguments are optional
        # if only speed [rotations/s] is given, the sign determines the direction
        # if abspos is given, the sign of the optional speed is ignored
        return self.move(abspos=abspos, speed=speed)


    def status(self):
        """ updates self.Status with the current status byte and returns it
        """
        self.reg(XACTUAL)
        return self.Status

    def stopped(self, drives=None):
        """ updates self.Status with the current status byte
            returns True if the motor is stopped
        """
        self.reg(XACTUAL)  # some read command to update the status
        return all([s & 0x08 for i,s in enumerate(self.Status) if drives is None or i in drives])

    def arrived(self, drives=None):
        """ updates self.Status with the current status byte
            returns True if the motor is at the target position
        """

        self.reg(XACTUAL)  # some read command to update the status
        return all([s & 0x20 for i,s in enumerate(self.Status) if drives is None or i in drives])

    def stalled(self, drives=None):
        """ updates self.Status with the current status byte
            returns True if ???
        """

        self.reg(XACTUAL)  # some read command to update the status
        return any([s & 0x04 for i,s in enumerate(self.Status) if drives is None or i in drives])

    def error(self, drives=None):
        """ updates self.Status with the current status byte
            returns True if the error bit is set
        """

        self.reg(XACTUAL)  # some read command to update the status
        return any([s & 0x02 for i,s in enumerate(self.Status) if drives is None or i in drives])

    def resetoccured(self, drives=None):
        """ updates self.Status with the current status byte
            returns True if a reset has occurred
        """

        self.reg(XACTUAL)  # some read command to update the status
        return any([s & 0x02 for i,s in enumerate(self.Status) if drives is None or i in drives])


    def TPWMTHRS(self, rps=None, drives=None):  # upper limit for stealth chop in rps
        pass

class Pump(Motor):
    """ takes driver/micro steps per milliliter as an initialization argument
        (remains accessible as F)
    """
    def __init__(self, stepspermilliliter):
        """ initializes the TMC5130
            sets the volume/step conversion factor
            zeroes the positive and negative totals and the position
        """
        self.F = stepspermilliliter
        self.TotalP = 0
        self.TotalM = 0
        Motor.__init__(self)
        self.Oldpos = self.move(relpos=0)