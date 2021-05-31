import detect
import pwm
import manual
import cv2

print("HOSGELDİNİZ.")
pwm0,pwm1,pwm2=pwm.main()
while True:
    try:
        selection = int(input("1-> Manuel Kullanım(Exit Q) 2-> Otonom Kullanım (Exit q) 3-> Çıkış"))
    except:
        pass
    if selection == 1:
        manual.main(pwm0,pwm1,pwm2)
    elif selection:
        detect.main(pwm0,pwm1)
    elif selection == 3:
        cv2.destroyAllWindows()
        break
    else:
        print("Lütfen geçerli bir değer giriniz.")
