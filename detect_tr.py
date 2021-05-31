import cv2,math,time
import numpy as np
import matplotlib.pyplot as plt
import RPi.GPIO as GPIO



# Kameradan alınan goruntu HSV formatına dönüştürülerek renk tonlarına maske uygulanır. Uygulanan maske ile kenarlar tespit edilir.
def kenar_algılama(goruntu):
    HSV = cv2.cvtColor(goruntu,cv2.COLOR_BGR2HSV)
    alt_deger= np.array([0,0,65])
    ust_deger= np.array([180,255,255])
    beyaz_maske = cv2.inRange(HSV,alt_deger,ust_deger)
    kenarlar = cv2.Canny(beyaz_maske,200,400)
    
    return kenarlar

# Şeritlerin bulunduğu yere göre tamamen maskeleme yapılır.
def ilgineline_bolge(kenarlar):
    yukseklik,genislik = kenarlar.shape
    maske = np.zeros_like(kenarlar)
    dikdortgen = np.array([[(0, yukseklik * 1 / 2),(genislik, yukseklik * 1 / 2),(genislik, yukseklik),(0, yukseklik),]], np.int32)
    cv2.fillPoly(maske,dikdortgen,255)
    maskelenen_bolge = cv2.bitwise_and(kenarlar,maske)
    
    return maskelenen_bolge

#  HoughLinesP formatı ile şerit parçalarının koordinatları elde edilir.
def bulunacak_serit_koordinatlari(maskelenen_bolge):
    serit_koordinatlari = cv2.HoughLinesP(maskelenen_bolge,1,np.pi/180,10,np.array([]),minLineLength=8,maxLineGap=4)
    return serit_koordinatlari


# Bulunan koordinatlara göre(x1,y1,x2,y2) doğru parçaları çizilir.
def serit_ciz(goruntu,seritler,serit_rengi=(0,255,0),kalinlik=10):
    sifir_goruntu = np.zeros_like(goruntu)
    if seritler is not None:
        for i in seritler:
            for x1,y1,x2,y2 in i:
                cv2.line(sifir_goruntu, (x1, y1), (x2, y2), serit_rengi, kalinlik)
    son_goruntu = cv2.addWeighted(goruntu,0.8,sifir_goruntu,1,1)
    return son_goruntu
# Bulunan slope(eğim) ve intercept(grafik 0 noktası) için nokta oluşturma.
def noktaları_olustur(goruntu, cizgi):
    yukseklik, genislik, _ = goruntu.shape
    egim, sifir_noktasi = cizgi
    y1 = yukseklik  # bottom of the goruntu
    y2 = int(y1 * 1 / 2)  # make points from middle of the goruntu down

    # bound the coordinates within the goruntu
    x1 = max(-genislik, min(2 * genislik, int((y1 - sifir_noktasi) / egim)))
    x2 = max(-genislik, min(2 * genislik, int((y2 - sifir_noktasi) / egim)))
    return [[x1, y1, x2, y2]]

# Her şerit için birden fazla doğru parçası tespit edildi. Bunun için ortalamaları alınıp tek bir çizgi elde edilir.
def egim_averaj(goruntu, serit_koordinatlari):
    seritler = []
    if serit_koordinatlari is None:
        return seritler
    yukseklik, genislik, _ = goruntu.shape
    sol_egim = []
    sag_egim = []

    bolge = 1/3
    sol_bolge = genislik * (1 - bolge)
    sag_bolge = genislik * bolge

    for serit_koordinat in serit_koordinatlari:
        for x1, y1, x2, y2 in serit_koordinat:
            if x1 == x2:
                continue
            fit = np.polyfit((x1, x2), (y1, y2), 1)
            egim = fit[0]
            sifir_noktasi = fit[1]
            if egim < 0:
                if x1 < sol_bolge and x2 < sol_bolge:
                    sol_egim.append((egim, sifir_noktasi))
            else:
                if x1 > sag_bolge and x2 > sag_bolge:
                    sag_egim.append((egim, sifir_noktasi))

    left_fit_avg = np.average(sol_egim, axis=0)
    if len(sol_egim) > 0:
        seritler.append(noktaları_olustur(goruntu, left_fit_avg))

    right_fit_avg = np.average(sag_egim, axis=0)
    if len(sag_egim) > 0:
        seritler.append(noktaları_olustur(goruntu, right_fit_avg))
    
    return seritler

def aci_hesaplama(goruntu, seritler):
    if len(seritler) == 0:
        return -90
    yukseklik, genislik, _ = goruntu.shape
    if len(seritler) == 1:
        x1, _, x2, _ = seritler[0][0]
        x_orta = x2 - x1
    else:
        _, _, left_x2, _ = seritler[0][0]
        _, _, right_x2, _ = seritler[1][0]
        bolge = 0.02 # 0.0 means car pointing to center, -0.03: car is centered to left, +0.03 means car pointing to right
        kamera_orta = int(genislik / 2 * (1 + bolge))
        x_orta = (left_x2 + right_x2) / 2 - kamera_orta


    y_orta = int(yukseklik / 2)

    aci_radyan = math.atan(x_orta / y_orta)  # angle (in radian) 
    aci_derece = int(aci_radyan * 180.0 / math.pi)  # angle (in degrees) 
    aci = aci_derece + 90  # this is the steering angle

    return aci

# Hesaplanan direksiyon açıları tamamen kararlı olmadığından stabilizastyon yapılır.
def stabilize_aci(duty,aci, yeni_aci, serit_sayisi, ikiserit_max_artis=5, birserit_max_artis=1):
    if serit_sayisi == 2 :
        # if both lane lines detected, then we can deviate more
        aci_max_artis = ikiserit_max_artis
    else :
        # if only one lane detected, don't deviate too much
        aci_max_artis = birserit_max_artis
    
    aci_artis = yeni_aci - aci
    if abs(aci_artis) > aci_max_artis:
        stabil_aci = int(aci + aci_max_artis * aci_artis / abs(aci_artis))
    else:
        stabil_aci = yeni_aci
    return stabil_aci

def direksiyon(aci,in1,in2,pwm0,pwm1):
    x=55
    y=53
    if aci <= 85 and aci > 80:
        ilerleme = "SOL" 
        GPIO.output(in1,GPIO.HIGH)
        GPIO.output(in2,GPIO.LOW)
        pwm1.ChangeDutyCycle(y)
        pwm0.ChangeDutyCycle(6.8)
    elif aci <= 80 and aci > 75:
        ilerleme = "SOL" 
        GPIO.output(in1,GPIO.HIGH)
        GPIO.output(in2,GPIO.LOW)
        pwm1.ChangeDutyCycle(y)
        pwm0.ChangeDutyCycle(6.5)
    elif aci <= 75 and aci > 70:
        ilerleme = "SOL"
        GPIO.output(in1,GPIO.HIGH)
        GPIO.output(in2,GPIO.LOW)
        pwm1.ChangeDutyCycle(y)
        pwm0.ChangeDutyCycle(6.2)
    elif aci <= 70 and aci > 65:
        ilerleme = "SOL" 
        GPIO.output(in1,GPIO.HIGH)
        GPIO.output(in2,GPIO.LOW)
        pwm1.ChangeDutyCycle(y)
        pwm0.ChangeDutyCycle(5.9)
    elif aci <= 65 and aci > 60:
        ilerleme = "SOL" 
        GPIO.output(in1,GPIO.HIGH)
        GPIO.output(in2,GPIO.LOW)
        pwm1.ChangeDutyCycle(y)
        pwm0.ChangeDutyCycle(5.7)
    elif aci <= 60 and aci > 55:
        ilerleme = "SOL" 
        GPIO.output(in1,GPIO.HIGH)
        GPIO.output(in2,GPIO.LOW)
        pwm1.ChangeDutyCycle(y)
        pwm0.ChangeDutyCycle(5.6)
    elif aci <= 55 and aci > 50:
        ilerleme = "SOL" 
        GPIO.output(in1,GPIO.HIGH)
        GPIO.output(in2,GPIO.LOW)
        pwm1.ChangeDutyCycle(y)
        pwm0.ChangeDutyCycle(5.3)
    elif aci <= 50 and aci > 45:
        ilerleme = "SOL" 
        GPIO.output(in1,GPIO.HIGH)
        GPIO.output(in2,GPIO.LOW)
        pwm1.ChangeDutyCycle(y)
        pwm0.ChangeDutyCycle(5)
    elif aci <= 45 and aci > 40:
        ilerleme = "SOL" 
        GPIO.output(in1,GPIO.HIGH)
        GPIO.output(in2,GPIO.LOW)
        pwm1.ChangeDutyCycle(y)
        pwm0.ChangeDutyCycle(4.7)
    elif aci < 40:
        ilerleme = "SOL" 
        GPIO.output(in1,GPIO.HIGH)
        GPIO.output(in2,GPIO.LOW)
        pwm1.ChangeDutyCycle(y)
        pwm0.ChangeDutyCycle(4.7)
    elif aci > 95 and aci < 100:
        ilerleme = "SAG" 
        GPIO.output(in1,GPIO.HIGH)
        GPIO.output(in2,GPIO.LOW)
        pwm1.ChangeDutyCycle(y)
        pwm0.ChangeDutyCycle(7.3)
    elif aci >= 100 and aci <105:
        ilerleme = "SAG" 
        GPIO.output(in1,GPIO.HIGH)
        GPIO.output(in2,GPIO.LOW)
        pwm1.ChangeDutyCycle(y)
        pwm0.ChangeDutyCycle(7.6)
    elif aci >= 105 and aci < 110:
        ilerleme = "SAG" 
        GPIO.output(in1,GPIO.HIGH)
        GPIO.output(in2,GPIO.LOW)
        pwm1.ChangeDutyCycle(y)
        pwm0.ChangeDutyCycle(7.9)
    elif aci >= 110 and aci < 115:
        ilerleme = "SAG" 
        GPIO.output(in1,GPIO.HIGH)
        GPIO.output(in2,GPIO.LOW)
        pwm1.ChangeDutyCycle(y)
        pwm0.ChangeDutyCycle(8.2)
    elif aci >= 115 and aci <120:
        ilerleme = "SAG" 
        GPIO.output(in1,GPIO.HIGH)
        GPIO.output(in2,GPIO.LOW)
        pwm1.ChangeDutyCycle(y)
        pwm0.ChangeDutyCycle(8.5)
    elif aci >= 120 and aci <125:
        ilerleme = "SAG" 
        GPIO.output(in1,GPIO.HIGH)
        GPIO.output(in2,GPIO.LOW)
        pwm1.ChangeDutyCycle(y)
        pwm0.ChangeDutyCycle(8.8)
    elif aci >= 125 and aci <130:
        ilerleme = "SAG" 
        GPIO.output(in1,GPIO.HIGH)
        GPIO.output(in2,GPIO.LOW)
        pwm1.ChangeDutyCycle(y)
        pwm0.ChangeDutyCycle(9.1)
    elif aci >= 130:
        ilerleme = "SAG" 
        GPIO.output(in1,GPIO.HIGH)
        GPIO.output(in2,GPIO.LOW)
        pwm1.ChangeDutyCycle(y)
        pwm0.ChangeDutyCycle(9.4)
    else:
        ilerleme = "DUZ" 
        GPIO.output(in1,GPIO.HIGH)
        GPIO.output(in2,GPIO.LOW)
        pwm1.ChangeDutyCycle(x)
        pwm0.ChangeDutyCycle(7)
    return ilerleme

def orta_cizgi_ciz(goruntu, aci, serit_rengi=(0, 0, 255), kalinlik=5 ):
    bos_goruntu = np.zeros_like(goruntu)
    yukseklik, genislik, _ = goruntu.shape

    # Note: the angle of:
    # 0-85 degree: turn left
    # 85-95 degree: going straight
    # 95-180 degree: turn right 
    aci_radyan = aci / 180.0 * math.pi
    x1 = int(genislik / 2)
    y1 = yukseklik
    x2 = int(x1 - yukseklik / 2 / math.tan(aci_radyan))
    y2 = int(yukseklik / 2)

    cv2.line(bos_goruntu, (x1, y1), (x2, y2), serit_rengi, kalinlik)
    son_goruntu = cv2.addWeighted(goruntu, 0.8, bos_goruntu, 1, 1)

    return son_goruntu

def HCR(trig,echo):
    GPIO.output(trig, False)
    GPIO.output(trig, True)
    time.sleep(0.00001)
    GPIO.output(trig, False)

    while GPIO.input(echo)==0:
        pulse_baslangic = time.time()

    while GPIO.input(echo)==1:
        pulse_bitis = time.time()

    pulse_suresi = pulse_bitis - pulse_baslangic

    uzunluk = pulse_suresi * 17150
    uzunluk = round(uzunluk, 2)
    return uzunluk
def dur(pwm1):
    pwm1.ChangeDutyCycle(0)
def bitir(pwm0,pwm1):
    pwm0.ChangeDutyCycle(0)
    pwm1.ChangeDutyCycle(0)

def main(pwm0,pwm1):
    in1,in2,echo,trig=3,4,20,21
    varsayilan_aci = 90
    camera = cv2.VideoCapture(0)

    while True:
        ret,goruntu = camera.read()
        
        kenar = kenar_algılama(goruntu)

        ilgilenilen_bolges = ilgineline_bolge(kenar)

        serit_koordinatlari = bulunacak_serit_koordinatlari(ilgilenilen_bolges)

        serit_koordinatlar = egim_averaj(goruntu, serit_koordinatlari)

        yonlendirme_acisi = aci_hesaplama(goruntu,serit_koordinatlar)

        stabil_aci = stabilize_aci(7,varsayilan_aci,yonlendirme_acisi,len(serit_koordinatlar))

        son_goruntu = orta_cizgi_ciz(goruntu, stabil_aci)
        
        uzunluk =HCR(trig,echo)
        
        if uzunluk < 50:
            dur(pwm1)
        else:
            ilerleme = direksiyon(stabil_aci,in1,in2,pwm0,pwm1)
        

        print("YÖN-> " + ilerleme)
        print("Direksiyon Açısı: %s" % stabil_aci)

        cv2.imshow("Goruntu",goruntu)
        cv2.imshow("Calisma Goruntusu",son_goruntu)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            bitir(pwm0,pwm1)
            break

    camera.release()
    cv2.destroyAllWindows()