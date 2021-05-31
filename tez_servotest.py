import RPi.GPIO as GPIO
from time import sleep


GPIO.SETMODE(GPIO.BCM)
GPIO.setup(17,GPIO.OUT)

#PWM ayarlama.  fPWM = 50Hz
pwm = GPIO.PWM(17,50)
pwm.start(0)

# PWM duty cycle 2-7 değerleri arasında 0-90 derece 7-12 değerleri arasında 90-180 derece değerlerini alır.
while True:
    try:
        secim = int(input( '1: Sol     2: Orta     3: Sağ     4:Çıkış'))
    except:
        print("HATA")
    if secim == 1:
        pwm.ChangeDutyCycle(3)
    elif secim == 2:
        pwm.ChangeDutyCycle(7)
    elif secim == 3:
        pwm.ChangeDutyCycle(11)
    elif secim == 4:
        pwm.ChangeDutyCycle(7)
        print("Başarıyla sonlandırıldı.....")
        break
    else:
        print("Geçerli değer giriniz.")

