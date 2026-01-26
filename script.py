import cv2 as reader
import mediapipe as mp
from math import sqrt

# Initialising the camera object
camera = reader.VideoCapture(0)
camera.set(3, 640)
camera.set(4, 480)

# Initialising stuff for Mediapipe
BaseOptions = mp.tasks.BaseOptions
model_path = r"C:\Coding\Projects\arm_project\gesture_recognizer.task"
options = mp.tasks.vision.GestureRecognizerOptions(base_options = BaseOptions(model_asset_path = model_path),
                                                   num_hands = 1,
                                                   running_mode = mp.tasks.vision.RunningMode.IMAGE)
recogniser = mp.tasks.vision.GestureRecognizer.create_from_options(options)


# -----------------------------------------------------------------------------------------------------------------------------------------------
# Global State Variables
startFlag = False
isPlaying = False
last_toggle_gesture = None  # To prevent flickering (debounce)

def sendCommands(recogniser_result):
    global startFlag, isPlaying, last_toggle_gesture
    
    # 1. Accessing data from the nested structure
    gestures = recogniser_result.gestures[0]  # List of candidates for hand 0
    top_gesture = gestures[0]
    gesture_name = top_gesture.category_name
    
    # Logic for start/ stop (victory symbol)
    if gesture_name == 'Victory':
        if last_toggle_gesture != 'Victory':
            startFlag = not startFlag
            print(f"System Status: {'STARTED' if startFlag else 'STOPPED'}")
            last_toggle_gesture = 'Victory'
    
    # Logic for playing and pausing (close-fist)
    elif gesture_name == 'Closed_Fist':
        if last_toggle_gesture != 'Closed_Fist':
            if startFlag:
                isPlaying = not isPlaying
                print(f"Media Status: {'PLAYING' if isPlaying else 'PAUSED'}")
            last_toggle_gesture = 'Closed_Fist'
            
    # Logic for volume comtrol(pinch)
    elif startFlag:
        last_toggle_gesture = None
        
        landmarks = recogniser_result.hand_landmarks[0]
        
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        
        distance = sqrt(
            (thumb_tip.x - index_tip.x)**2 + 
            (thumb_tip.y - index_tip.y)**2
        )
        
        # Simple threshold for a 'pinch'
        if distance < 0.05:
            # print("Pinch detected! Volume adjusting...")
            pass

    else:
        # Reset debounce when hand is visible but doing nothing special
        last_toggle_gesture = None

# -----------------------------------------------------------------------------------------------------------------------------------------------

while True:
    _, frame = camera.read()
    if not _:
        continue

    # Converting the frame for mediapipe to work upon.
        # Convert BGR frame to RGB frame
    frame_RGB = reader.cvtColor(frame, reader.COLOR_BGR2RGB)
        # Mediapipe needs the image in a mpImage format.
    mediapipe_img = mp.Image(mp.ImageFormat.SRGB, frame_RGB)

    recogniser_result = recogniser.recognize(mediapipe_img)

    if recogniser_result.gestures:
        # The switchcase function
        sendCommands(recogniser_result)
    else:
        reader.putText(frame, "No hand detected", (15, 50), reader.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 1, reader.LINE_AA)

    # Show the original BGR frame (OpenCV expects BGR for imshow)
    reader.imshow("Camera", frame)
    
    if reader.waitKey(1) == ord('q'):
        break


# Cleaning
recogniser.close()
camera.release()
reader.destroyAllWindows()