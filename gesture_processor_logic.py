from math import sqrt
import cv2
import time
from OneEuroFilter import OneEuroFilter

# Connecting to other files:
from input_handler import async_typer
from utilities import GestureCooldown

class GestureProcessor:
    def __init__(self):
        # State Initialization
        self.pinch_start_coords = None
        self.base_gap_threshold = 0.05
        self.base_volume_sensitivity = 0.08
        self.isPlaying = False
        self.isSystemOn = False
        self.isMuted = False
        self.last_system_state = None 
        self.last_play_state = None
        self.last_vol_state = None
        self.user_hand_preference = "left" 
        
        # Cooldowns
        self.toggle_cooldown = GestureCooldown(limit=1.0)
        self.volume_cooldown = GestureCooldown(limit=0.1)
        self.seeker_cooldown = GestureCooldown(limit=0.5)

        # OneEuroFilter
        self.config = {
            'freq': 30,      # frequency of the input signal (Hz)
            'mincutoff': 1.5, # Minimum cutoff to remove jitter
            'beta': 5,        # Reduces lag during fast movements
            'dcutoff': 1.0    # Cutoff frequency
        }

        self.filter = OneEuroFilter(**self.config)

    def process_frame(self, result, frame):
        # 0. Trivial checks
        if not result or not result.gestures or len(result.gestures) == 0 or not result.handedness or len(result.handedness) == 0:
            self.reset_gesture_states()
            return
        
        # 0.5. Hand Preference Check 
        chosen_hand_idx = -1
        for i in range(len(result.handedness)):
            detected_handedness = result.handedness[i][0].category_name.lower()

            if detected_handedness == self.user_hand_preference.lower():
                chosen_hand_idx = i
                break
                
        # If the preferred hand wasn't found in this frame, exit early
        if chosen_hand_idx == -1:
            self.reset_gesture_states()
            return
        
        # Visual Feedback for detected preferred hand
        h, w, _ = frame.shape
        wrist = result.hand_landmarks[chosen_hand_idx][0]
        cv2.circle(frame, (int(wrist.x * w), int(wrist.y * h)), 5, (0, 255, 255), 2)
        cv2.putText(frame, "chosen hand", (int(result.hand_landmarks[chosen_hand_idx][0].x * frame.shape[1]), int(result.hand_landmarks[chosen_hand_idx][0].y * frame.shape[0])), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 1)
        
        # 0.75. Distance Scaling
        hand_landmarks = result.hand_landmarks[chosen_hand_idx]
        wrist = hand_landmarks[0]
        middle_mcp = hand_landmarks[9]
        hand_size = sqrt((middle_mcp.x - wrist.x)**2 + (middle_mcp.y - wrist.y)**2)
        
        scale_factor = 0.15 / max(hand_size, 0.1)
        scale_factor = max(0.5, min(scale_factor, 3.0)) 

        gap_threshold = self.base_gap_threshold / scale_factor
        volume_sensitivity = self.base_volume_sensitivity / scale_factor

        # 1. Accessing gesture data for the chosen hand
        gestures = result.gestures[chosen_hand_idx]
        top_gesture = gestures[0]
        gesture_name = top_gesture.category_name

        # 2. Action categories
        
        # --- Start/Stop Logic ---
        if gesture_name == 'Victory':
            target_state = "Started" if not self.isSystemOn else "Stopped"
            if self.last_system_state != target_state and self.toggle_cooldown.ready():
                self.isSystemOn = not self.isSystemOn
                print("Recognition started." if self.isSystemOn else "Recognition stopped.")
                if not self.isSystemOn: async_typer("`")
                self.last_system_state = target_state
            
            self.last_play_state = None 
            self.pinch_start_coords = None
            return "Recognition started" if self.isSystemOn else "Recognition stopped"
        
        # --- Rest gesture ---
        elif gesture_name == 'Open_Palm':
            pass
        
        # --- Mute/Unmute Logic ---
        elif gesture_name == 'Closed_Fist' and self.isSystemOn:
            target_vol_state = "Muted" if not self.isMuted else "Unmuted"
            if self.last_vol_state != target_vol_state and self.toggle_cooldown.ready():
                self.isMuted = not self.isMuted
                print("Volume status: " + ("Muted" if self.isMuted else "Unmuted"))
                async_typer("m")
                self.last_vol_state = target_vol_state
            self.last_system_state = None
            self.pinch_start_coords = None
            return "Muted" if self.isMuted else "Unmuted"

        # --- Play/Pause Logic ---
        elif gesture_name == 'Pointing_Up' and self.isSystemOn:
            target_play = "Playing" if not self.isPlaying else "Paused"
            if self.last_play_state != target_play and self.toggle_cooldown.ready():
                self.isPlaying = not self.isPlaying
                print("Video status: " + ("Playing" if self.isPlaying else "Paused"))
                async_typer("space")
                self.last_play_state = target_play
            self.last_system_state = None
            self.pinch_start_coords = None
            return "Video " + ("played" if self.isPlaying else "paused")

        # --- Seekbar Control Logic ---
        elif gesture_name == 'Thumb_Up' and self.isSystemOn:
            if self.seeker_cooldown.ready():
                print("Seeked forward.")
                async_typer("right")
            self.last_system_state = None
            self.pinch_start_coords = None
            return "Seeked forward"
        
        elif gesture_name == 'Thumb_Down' and self.isSystemOn:
            if self.seeker_cooldown.ready():
                print("Seeked backward.") 
                async_typer("left")
            self.last_system_state = None
            self.pinch_start_coords = None
            return "Seeked backward"

        # --- Volume Control Logic ---
        elif self.isSystemOn:
            action_text_to_send = None
            thumb_tip = hand_landmarks[4]
            index_tip = hand_landmarks[8]

            unfiltered_distance = sqrt((thumb_tip.x - index_tip.x)**2 + (thumb_tip.y - index_tip.y)**2)
            filtered_distance = self.filter(unfiltered_distance, timestamp=int(time.time() * 1000000))
            current_pinch_position = ((thumb_tip.x + index_tip.x) / 2, (thumb_tip.y + index_tip.y) / 2)

            if filtered_distance <= gap_threshold:
                if self.pinch_start_coords is None:
                    self.pinch_start_coords = current_pinch_position
                else:
                    y_movement = self.pinch_start_coords[1] - current_pinch_position[1]

                    if (abs(y_movement) > volume_sensitivity) and (self.volume_cooldown.ready()):
                        async_typer("up" if y_movement > 0 else "down")
                        print("Volume up." if y_movement > 0 else "Volume down.")
                        action_text_to_send = "Volume increased" if y_movement > 0 else "Volume decreased"
                        self.pinch_start_coords = current_pinch_position 
                
                h, w, _ = frame.shape
                cv_pos = (int(current_pinch_position[0] * w), int(current_pinch_position[1] * h))
                cv2.circle(frame, cv_pos, 5, (0, 255, 255), -1)
            else:
                self.pinch_start_coords = None
            return action_text_to_send
        else:
            self.reset_gesture_states()

    def reset_gesture_states(self):
        """Helper to clear temporary tracking states when hand is lost or system is off."""
        self.pinch_start_coords = None
        self.last_system_state = None
        self.last_play_state = None