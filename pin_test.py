import board
import digitalio
import time

p = digitalio.DigitalInOut(board.D5)
p.switch_to_output(True)

while True:
    p.value = not p.value
    print(p.value)
    time.sleep(2)