'''
checking a single mmplex stepper board via SPI
'''
import sys
import os
import time
import board
import lis_circuitpython_tmc5130 as tmc

import conf

print('kill -SIGINT', os.getpid())

conf.gpio_3v_enable.value = True
def pstat(m):
    print(f'{m.status():08b}  XTARGET {m.reg(tmc.XTARGET):12d}  XACTUAL {m.reg(tmc.XACTUAL):12d}  XLATCH {m.reg(tmc.XLATCH):12d}  RAMP_STAT {m.reg(tmc.RAMP_STAT):013b}')

print(dir(board))

try:
    num_of_motors=4
    mots = []
    for i in range(num_of_motors):
        mots.append(
            tmc.Motor(conf.spi_dock, chip_select=conf.cs_dock, gconf=0b110, ihold_irun=0x01_04_00, num_of_motors=num_of_motors, motor_num=i, baudrate=500_000)
        )

    for m in mots:
        #m = mots[1]
        print('Error = ', m.error)
        '''if m.error:
            sys.exit()'''

        time.sleep(0.1)

        # set motor currents
        # b02: stealth chop
        # b01: use internal sense resistors
        m.reg(tmc.GCONF, 0b110) #  # b2=stealthchop,b1=internal sense resistors, b0=0
        m.reg(tmc.IHOLD_IRUN, 0x01_10_00)  # IHOLDDELAY=1, IRUN=(4+1)/32 IHOLD=(0+1)/32
        m.reg(tmc.AMAX, 2000)
        m.reg(tmc.DMAX, 1000)

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

        m.reg(tmc.XACTUAL, 1_000_000)
        pstat(m)
        if m.switch_left():
            bt = 15
            print(f'end switch pressed, backtracking {bt}°')
            print(m.moveby(int(532_480 / 360 * 30), int(532_480 / 10)))
            while not m.arrived():
                pass

        print(m.moveby(int(-532_480/360*90), int(532_480/20)))
        print('searching for end switch')
        time_out = time.time() + 10
        t_print = time.time() + 0.5
        timed_out = False
        arrived = False
        endswitch = False
        while True:
            # print position every 0.5 seconds
            if time.time() > t_print:
                pstat(m)
                t_print = time.time() + 0.5
            # break if arriving w/o hitting end switch
            if arrived := m.arrived():
                break
            # break if timing out
            elif timed_out := time.time() > time_out:
                break
            # break if stopped after hitting end switch
            elif endswitch := m.switch_left():
                break

        if timed_out:
            print('timed out')
        elif arrived:
            print('end switch not found')
        elif endswitch:
            print('endswitch hit')
            pstat(m)
            # move to XLATCH
            m.moveto(m.reg(tmc.XLATCH), int(532_480 / 10))
            while not m.arrived():
                pstat(m)
            #set home position
            print('set home position')
            m.reg(tmc.XACTUAL, 0)
            m.reg(tmc.XTARGET, 0)

            pstat(m)


    for _ in range(3):
        while True:
            i = input('proceed (y/n)?')
            if i in ('ynYN'):
                break
        if i in 'Nn':
            break
        for m in mots:

            print(m.moveto(int(532_480 / 360 * 93), int(532_480 / 10)))
            while not m.arrived():
                pass
            time.sleep(1)

            pstat(m)

            print(m.moveto(int(532_480 / 360 * 7), int(532_480 / 10)))
            while not (m.arrived() or m.switch_left()):
                pass
            print(m.moveto(int(532_480 / 360 * 0), int(532_480 / 100)))
            while True:
                switch = m.switch_left()
                arrived = m.arrived()
                if switch or arrived:
                    break

            pstat(m)
            # re-home
            if switch:
                print('re-home')
                m.moveto(m.reg(tmc.XLATCH), int(532_480 / 50))
                while not m.arrived():
                    pass
                m.reg(tmc.XACTUAL, 0)
                m.reg(tmc.XTARGET, 0)

            time.sleep(1)

    for m in mots:
        m.moveby(0, int(532_480/10))
    print('Done')
    sys.exit()

finally:
    print('cleaning up')
    conf.cs_dock.switch_to_input()
    conf.cs_dock.deinit()
    conf.spi_dock.deinit()


