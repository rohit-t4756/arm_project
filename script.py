import cv2 as reader
import mediapipe as mp
import os
import time
from math import sqrt
from threading import Thread, Lock
from pynput.keyboard import Key, Controller

# Utility classes
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

class PerformanceMonitor:
    def __init__(self):
        self.inference_times = []
        self.total_latencies = []
        self.fps = 0
        self.last_fps_update = time.time()
        self.frame_count = 0

    def update(self, t_start, t_end):
        total_ms = (t_end - t_start) * 1000
        self.total_latencies.append(total_ms)
        
        if len(self.total_latencies) > 30:
            self.total_latencies.pop(0)
            
        self.frame_count += 1
        if time.time() - self.last_fps_update > 1.0:
            self.fps = self.frame_count
            self.frame_count = 0
            self.last_fps_update = time.time()

    def get_stats(self):
        avg_total = sum(self.total_latencies) / len(self.total_latencies) if self.total_latencies else 0
        return self.fps, avg_total

monitor = PerformanceMonitor()

# Global State ----------------
pinch_start_coords = None
gap_threshold = 0.05
volume_sensitivity = 0.08
isPlaying = False
isSystemOn = False
last_system_state = None 
last_play_state = None
user_hand_preference = "left"
toggle_cooldown = GestureCooldown(limit=1.5)
volume_cooldown = GestureCooldown(limit=0.1)


# Mapping for pynput keys ----------------
keyboard = Controller()

KEY_MAP = {
    "space"    :Key.space,
    "up"       :Key.up,
    "down"     :Key.down,
    "q"        :'q'
}

def async_typer(key_name):
    """
    Uses pynput to press keys. 
    pynput's Controller is thread-safe for simple tap operations.
    """
    def press():
        try:
            target_key = KEY_MAP.get(key_name, key_name)
            keyboard.press(target_key)
            keyboard.release(target_key)
        except Exception as e:
            print(f"Pynput Error: {e}")
            
    # Corrected function reference pass
    Thread(target=press, daemon=True).start()


# Result storage for the async callback ----------------
latest_result = None
result_lock = Lock()

# Live stream callback function
def result_callback(result_obj, inp_img, timestamp):
    global latest_result
    with result_lock:
        latest_result = result_obj
    pass


# Initialising system ---------------
camera = reader.VideoCapture(0)
camera.set(3, 640)      # PropertyId 3: Frame width
camera.set(4, 480)      # PropertyId 4: Frame height

BaseOptions = mp.tasks.BaseOptions
model_path = "gesture_recognizer.task"
if not os.path.exists(model_path):
    model_path = os.path.expanduser("~/arm/arm_project/gesture_recognizer.task")
options = mp.tasks.vision.GestureRecognizerOptions(base_options = BaseOptions(model_asset_path = model_path),
                                                   num_hands = 1,
                                                   running_mode = mp.tasks.vision.RunningMode.LIVE_STREAM,
                                                   result_callback = result_callback)

recogniser = mp.tasks.vision.GestureRecognizer.create_from_options(options)


# Process image ----------------
def process_image(result, frame):
    global pinch_start_coords, gap_threshold, volume_sensitivity, isPlaying, isSystemOn, last_system_state, last_play_state, user_hand_preference

    # 0. Trivial checks
    if not result or not result.gestures or len(result.gestures) == 0 or not result.handedness or len(result.handedness) == 0:
        pinch_start_coords = None
        last_system_state = None
        last_play_state = None
        return
    
    # 0.5. Ensure only user selected hand can be used to update the state.
    if result.handedness[0][0].category_name.lower() != user_hand_preference.lower():
        pinch_start_coords = None
        last_system_state = None
        last_play_state = None
        return

    # 1. Accessing the data
    gestures = result.gestures[0]
    top_gesture = gestures[0]
    gesture_name = top_gesture.category_name

    # 2. Action categories
    # Start Stop logic
    if (gesture_name == 'Victory'):
        target_state = "Started" if not isSystemOn else "Stopped"
        if last_system_state != target_state and toggle_cooldown.ready():
            isSystemOn = not isSystemOn
            print("Recognition started." if isSystemOn else "Recognition stopped.")
            if not isSystemOn: async_typer("q")
            last_system_state = target_state
        last_play_state = None 
        pinch_start_coords = None

    # --- Play Pause logic (Only if system is ON) ---
    elif (gesture_name == 'Closed_Fist' and isSystemOn):
        target_play = "Playing" if not isPlaying else "Paused"
        if last_play_state != target_play and toggle_cooldown.ready():
            isPlaying = not isPlaying
            print("Video status: " + ("Playing" if isPlaying else "Paused"))
            async_typer("space")
            last_play_state = target_play
        last_system_state = None
        pinch_start_coords = None

    # Volume control logic
    elif isSystemOn:
        hand_landmarks = result.hand_landmarks[0]
        thumb_tip = hand_landmarks[4]
        index_tip = hand_landmarks[8]

        distance = sqrt((thumb_tip.x - index_tip.x)**2 + (thumb_tip.y - index_tip.y)**2)
        current_pinch_position = ((thumb_tip.x + index_tip.x) / 2, (thumb_tip.y + index_tip.y) / 2)

        if distance <= gap_threshold:
            if pinch_start_coords == None:
                pinch_start_coords = current_pinch_position
            else:
                y_movement = pinch_start_coords[1] - current_pinch_position[1]

                if (abs(y_movement) > volume_sensitivity) and (volume_cooldown.ready()):
                    async_typer("up" if y_movement > 0 else "down")
                    print("Volume up." if y_movement > 0 else "Volume down.")
                    pinch_start_coords = current_pinch_position 
            
            # Overlay information.
            h, w, _ = frame.shape
            cv_pos = (int(current_pinch_position[0] * w), int(current_pinch_position[1] * h))
            reader.circle(frame, cv_pos, 8, (0, 255, 255), -1)
        else:
            pinch_start_coords = None
        pass
    else:
        last_system_state = None
        last_play_state = None
        pinch_start_coords = None


# Main Loop ----------------
while True:
    t_start = time.perf_counter()

    _, frame = camera.read()
    if not _: continue

    frame_RGB = reader.cvtColor(frame, reader.COLOR_BGR2RGB)
    mediapipe_image = mp.Image(image_format = mp.ImageFormat.SRGB, data = frame_RGB)

    # Send frame for recognition.
    timestamp_ms = int(time.time() * 1000000)
    recogniser.recognize_async(mediapipe_image, timestamp_ms)

    # Send the current global result for processing.
    with result_lock:
        current_result = latest_result

    process_image(current_result, frame)

    t_end = time.perf_counter()
    monitor.update(t_start, t_end)
    fps, total_ms = monitor.get_stats()

    # Overlay
    status_color = (0, 255, 0) if isSystemOn else (0, 255, 255)
    reader.putText(frame, f"LIVE_STREAM | FPS: {fps}", (15, 30), 1, 1.2, status_color, 2)
    reader.putText(frame, f"Latency: {total_ms:.1f}ms", (15, 60), 1, 1.2, (0, 255, 0) if total_ms < 200 else (0, 0, 255), 2)

    # Display:
    reader.imshow("Feed", frame)
    if reader.waitKey(1) == ord('q'): break

# Cleaning ----------------
recogniser.close()
camera.release()
reader.destroyAllWindows()