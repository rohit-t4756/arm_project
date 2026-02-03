from math import sqrt
import cv2

import time
from OneEuroFilter import OneEuroFilter

# Connecting to our other files:
from input_handler import async_typer
from utilities import GestureCooldown

class GestureProcessor:
    def __init__(self):
        # State Initialization (Previously Global Variables)
        self.pinch_start_coords = None
        self.gap_threshold = 0.05
        self.volume_sensitivity = 0.08
        self.isPlaying = False
        self.isSystemOn = False
        self.last_system_state = None 
        self.last_play_state = None
        self.user_hand_preference = "left"
        
        # Cooldowns
        self.toggle_cooldown = GestureCooldown(limit=1.5)
        self.volume_cooldown = GestureCooldown(limit=0.1)

        # OneEuroFilter
        self.config = {
            'freq': 30,      # frequency of the input signal (Hz, my case FPS).
            'mincutoff': 1.5, # Minimum cutoff FPS to remove jitter at slow speeds.
            'beta': 5,      # Reduces lag during fast movements.
            'dcutoff': 1.0    # Cutoff frequency.
        }

        self.filter = OneEuroFilter(**self.config)

    def process_frame(self, result, frame):
        # 0. Trivial checks
        if not result or not result.gestures or len(result.gestures) == 0 or not result.handedness or len(result.handedness) == 0:
            self.pinch_start_coords = None
            self.last_system_state = None
            self.last_play_state = None
            return
        
        # 0.5. Hand Preference Check
        if result.handedness[0][0].category_name.lower() != self.user_hand_preference.lower():
            self.pinch_start_coords = None
            self.last_system_state = None
            self.last_play_state = None
            return

        # 1. Accessing the data
        gestures = result.gestures[0]
        top_gesture = gestures[0]
        gesture_name = top_gesture.category_name

        # 2. Action categories
        
        # --- Start/Stop Logic ---
        if (gesture_name == 'Victory'):
            target_state = "Started" if not self.isSystemOn else "Stopped"
            if self.last_system_state != target_state and self.toggle_cooldown.ready():
                self.isSystemOn = not self.isSystemOn
                print("Recognition started." if self.isSystemOn else "Recognition stopped.")
                if not self.isSystemOn: async_typer("q")
                self.last_system_state = target_state
            
            self.last_play_state = None 
            self.pinch_start_coords = None

        # --- Play/Pause Logic ---
        elif (gesture_name == 'Closed_Fist' and self.isSystemOn):
            target_play = "Playing" if not self.isPlaying else "Paused"
            if self.last_play_state != target_play and self.toggle_cooldown.ready():
                self.isPlaying = not self.isPlaying
                print("Video status: " + ("Playing" if self.isPlaying else "Paused"))
                async_typer("space")
                self.last_play_state = target_play
            self.last_system_state = None
            self.pinch_start_coords = None

        # --- Volume Control Logic ---
        elif self.isSystemOn:
            hand_landmarks = result.hand_landmarks[0]
            thumb_tip = hand_landmarks[4]
            index_tip = hand_landmarks[8]

            unfiltered_distance = sqrt((thumb_tip.x - index_tip.x)**2 + (thumb_tip.y - index_tip.y)**2)
            filtered_distance = self.filter(unfiltered_distance, timestamp= int(time.time() * 1000000))
            current_pinch_position = ((thumb_tip.x + index_tip.x) / 2, (thumb_tip.y + index_tip.y) / 2)

            if filtered_distance <= self.gap_threshold:
                if self.pinch_start_coords == None:
                    self.pinch_start_coords = current_pinch_position
                else:
                    y_movement = self.pinch_start_coords[1] - current_pinch_position[1]

                    if (abs(y_movement) > self.volume_sensitivity) and (self.volume_cooldown.ready()):
                        async_typer("up" if y_movement > 0 else "down")
                        print("Volume up." if y_movement > 0 else "Volume down.")
                        self.pinch_start_coords = current_pinch_position 
                
                # Overlay information (Visual Feedback)
                h, w, _ = frame.shape
                cv_pos = (int(current_pinch_position[0] * w), int(current_pinch_position[1] * h))
                cv2.circle(frame, cv_pos, 5, (0, 255, 255), -1)
            else:
                self.pinch_start_coords = None
        else:
            self.last_system_state = None
            self.last_play_state = None
            self.pinch_start_coords = None