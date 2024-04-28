import cv2
cap = cv2.VideoCapture(0)
ret, im = cap.read()
cv2.imwrite("image.jpg", im)