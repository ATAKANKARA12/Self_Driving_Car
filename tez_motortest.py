import RPi.GPIO as GPIO

#GPIO Modu seçimi  BCM=PIN numaralarına göre adlandırılma yapılır.
GPIO.SETMODE(GPIO.BCM)

#Seçilen pini çıkış olarak ayarlar.
ena,in1,in2=2,3,4
GPIO.setup(ena,GPIO.OUT)
GPIO.setup(in1,GPIO.OUT)
GPIO.setup(in2,GPIO.OUT)

#PWM ayarlama.  PWM = 100Hz
p=GPIO.PWM(ena,100)

p.start(0)

# PWM duty cycle değeri 0-100 arasında çalışır ve motorun çalışma hızını belirler.
while True:
    try:
        secim = int(input("1: Saat Yönünde Sabit Hız  2:Dönme Hızını değiştir.   3:Saat Yönünün tersinde sabit hız 4: Çıkış"))
    except:
        print("HATA")
    if secim == 1:
        GPIO.output(in1,GPIO.HIGH)
        GPIO.output(in2,GPIO.LOW)
        p.ChangeDutyCycle(duty)
    elif secim == 2:
        duty = int(input("Yeni duty cycle (0->100(=!100 olmalıdır)):"))
    elif secim == 3:
        GPIO.output(in1,GPIO.LOW)
        GPIO.output(in2,GPIO.HIGH)
        p.ChangeDutyCycle(duty)
    elif secim == 4:
        p.ChangeDutyCycle(0)
        print("Başarıyla sonlandırıldı.....")
        break
    else:
        print("Geçerli değer giriniz.")
