import cv2
#Kamera açma işlemi. 0 Dahili kamerayı kullanır.
cap = cv2.VideoCapture(0)

res = int(input('1 PHOTO 2 VİDEO'))
if res == 1:
    #görüntüleri alma
    ret,frame = cap.read()
    #Fotoğrafı kaydetme
    cv2.imwrite("test.jpg",frame)
elif res == 2:
    while True:
        # görüntüleri alma
        ret,frame = cap.read()
        # görüntüleri ekranda gösterme
        cv2.imshow('IMAGE',frame)
        
        # Q ile çıkış yapma.
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    
cap.release()
cv2.destroyAllWindows()
