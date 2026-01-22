import cv2 as reader
import mediapipe as mp

# Initialising the camera object
camera = reader.VideoCapture(0)
camera.set(3, 640)
camera.set(4, 480)

while True:
    flag, frame = camera.read()
    if flag:
        reader.imshow("Camera", frame)
        if reader.waitKey(1) == ord('q'):
            break

reader.destroyAllWindows()