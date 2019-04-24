from pigpio import pi as rasp_pi, OUTPUT
from time import sleep

PIN = 17
DELAY = 4

pi = rasp_pi()
pi = rasp_pi()

pi.set_mode(PIN, OUTPUT)

pi.write(PIN, False)
print('Off')
sleep(DELAY)
pi.write(PIN, True)
print('On')
sleep(DELAY)
pi.write(PIN, False)
print('Off')
sleep(DELAY)
pi.write(PIN, True)
print('On')
sleep(DELAY)
pi.write(PIN, False)
print('Off')
sleep(2)

pi.stop()
