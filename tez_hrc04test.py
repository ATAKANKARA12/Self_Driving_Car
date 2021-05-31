import RPi.GPIO as GPIO
import time


GPIO.SETMODE(GPIO.BCM)

TRIG = 21
ECHO = 20

GPIO.setup(TRIG,GPIO.OUT)
GPIO.setup(ECHO,GPIO.IN)


while True:
    GPIO.output(TRIG, False)

    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    while GPIO.input(ECHO)==0:
        pulse_start = time.time()

    while GPIO.input(ECHO)==1:
        pulse_end = time.time()

    pulse_duration = pulse_end - pulse_start

    distance = pulse_duration * 17150
    distance = round(distance, 2)
    print('UZAKLIK: %s' % distance)
    if distance < 30:
        print('DUR')
    else:
        print('DEVAM ET')
