import cv2 as reader
import mediapipe as mp
from math import sqrt
import pyautogui as typer
import time
import threading

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
pinch_start_coords = ()
last_toggle_gesture = None  # To prevent flickering (debounce)

# Cooldown function
    # implement a function to send true after the time since call has reached time_limit.
class GestureCooldown:
    def __init__(self, limit=1.0):
        self.limit = limit
        self.last_call = 0

    def ready(self):
        now = time.perf_counter()
        if now - self.last_call >= self.limit:
            self.last_call = now
            return True
        return False


# Implement the typer function as an async function.
def async_typer(key):
    def press():
        try:
            typer.press(key)
        except Exception as e:
            print(f"Typer Error: {e}")
        
    thread = threading.Thread(target = press())
    thread.start()
    
# Initialize Global Managers
toggle_cooldown = GestureCooldown(limit=1.5)  # 1.5s between toggle actions
volume_cooldown = GestureCooldown(limit=0.1)  # 0.1s for smoother volume scrolling

def sendCommands(recogniser_result, frame):
    global startFlag, isPlaying, last_toggle_gesture, pinch_start_coords
    
    # 1. Accessing data from the nested structure
    gestures = recogniser_result.gestures[0]  # List of candidates for hand 0
    top_gesture = gestures[0]
    gesture_name = top_gesture.category_name
    
    # Logic for start/ stop (victory symbol)
    if gesture_name == 'Victory':
        if last_toggle_gesture != 'Victory' and toggle_cooldown.ready():
            startFlag = not startFlag
            print(f"System Status: {'STARTED' if startFlag else 'STOPPED'}")
            if not startFlag:
                async_typer("q")
            last_toggle_gesture = 'Victory'

    
    # Logic for playing and pausing (close-fist)
    elif gesture_name == 'Closed_Fist':
        if last_toggle_gesture != 'Closed_Fist' and startFlag and toggle_cooldown.ready():
            isPlaying = not isPlaying
            print(f"Media Status: {'PLAYING' if isPlaying else 'PAUSED'}")
            async_typer("space")
            last_toggle_gesture = 'Closed_Fist'
            
    # Logic for volume comtrol(pinch)
    elif startFlag:
        last_toggle_gesture = None
        landmarks = recogniser_result.hand_landmarks[0]
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        
        finger_gap = sqrt((thumb_tip.x - index_tip.x)**2 + (thumb_tip.y - index_tip.y)**2)
        average = ((thumb_tip.x + index_tip.x) / 2, (thumb_tip.y + index_tip.y) / 2)
        
        # Adjusting distance threshold slightly for reliability
        if finger_gap < 0.05: 
            if pinch_start_coords is None:
                pinch_start_coords = average
            else:
                delta_y = pinch_start_coords[1] - average[1]
                sensitivity = 0.08 
                
                if abs(delta_y) > sensitivity and volume_cooldown.ready():
                    if delta_y > 0:
                        async_typer("up")
                        print("Volume +")
                    else:
                        async_typer("down")
                        print("Volume -")
                    pinch_start_coords = average # Update anchor
            
            # Draw visual feedback (Converting normalized to pixel coordinates)
            h, w, _ = frame.shape
            pixel_center = (int(average[0] * w), int(average[1] * h))
            reader.circle(frame, pixel_center, 5, (1, 92, 255), -1)
        else:
            pinch_start_coords = None
    else:
        # Reset debounce when hand is visible but doing nothing special
        last_toggle_gesture = None
        pinch_start_coords = None

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
        sendCommands(recogniser_result, frame)
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
