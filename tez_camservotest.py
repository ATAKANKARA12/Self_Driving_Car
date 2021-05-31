import RPi.GPIO as GPIO
from time import sleep

#GPIO Modu seçimi  BCM=PIN numaralarına göre adlandırılma yapılır.
GPIO.SETMODE(GPIO.BCM)
#Seçilen pini çıkış olarak ayarlar.
GPIO.setup(5,GPIO.OUT)

#PWM ayarlama.  PWM = 50Hz
pwm = GPIO.PWM(5,50)
pwm.start(0)



# PWM duty cycle 2-7 değerleri arasında saat yönünde 7-12 değerleri arasında saat yönünün tersinde döner.
while True:
    try:
        secim = int(input("1: Saat Yönünde  2:Durdur   3:Saat Yönünün tersinde dönüş 4: Çıkış"))
    except:
        print("HATA")
    if secim == 1:
        pwm.ChangeDutyCycle(5)
    elif secim == 2:
        pwm.ChangeDutyCycle(7)
    elif secim == 3:
        pwm.ChangeDutyCycle(9)
    elif secim == 4:
        pwm.ChangeDutyCycle(7)
        print("Başarıyla sonlandırıldı.....")
        break
    else:
        print("Geçerli değer giriniz.")
print("END")
