from math import sqrt
import cv2
import time
from OneEuroFilter import OneEuroFilter
from input_handler import async_typer
from utilities import GestureCooldown

class GestureProcessor:
    def __init__(self):
        # State Initialization
        self.pinch_start_coords = None
        self.base_gap_threshold = 0.05
        self.base_volume_sensitivity = 0.1
        self.isSystemOn = False
        self.isMuted = False
        
        # Default Settings
        self.user_hand_preference = "Left"
        
        # Gesture Mapping Variable (UI action name -> MediaPipe Gesture Name)
        self.gesture_map = {
            "System Toggle": "Victory",
            "Play/Pause": "Pointing_Up",
            "Mute Toggle": "Closed_Fist",
            "Seek forward": "Thumb_Up",
            "Seek backward": "Thumb_Down",
            "Rest": "Open_Palm"
        }
        
        # Cooldowns
        self.toggle_cooldown = GestureCooldown(limit=0.6)
        self.volume_cooldown = GestureCooldown(limit=0.05)
        self.seeker_cooldown = GestureCooldown(limit=0.05)

        # Filtering
        self.filter = OneEuroFilter(freq=30, mincutoff=1.5, beta=5, dcutoff=1.0)

    def update_config(self, config):
        """Updates internal variables based on a settings dictionary."""
        # 1. Update Hand Preference
        self.user_hand_preference = config.get("hand_preference", "Left")
        
        # 2. Update Cooldowns
        cooldowns = config.get("cooldowns", {})
        if "Toggle cooldown" in cooldowns:
            self.toggle_cooldown.limit = cooldowns["Toggle cooldown"]
        if "Volume cooldown" in cooldowns:
            self.volume_cooldown.limit = cooldowns["Volume cooldown"]
        if "Seekbar cooldown" in cooldowns:
            self.seeker_cooldown.limit = cooldowns["Seekbar cooldown"]
            
        # 3. Update Gesture Mappings
        ui_to_internal = {
            "Open palm": "Open_Palm",
            "Victory": "Victory",
            "Pointing up": "Pointing_Up",
            "Fist": "Closed_Fist",
            "Thumb up": "Thumb_Up",
            "Thumb down": "Thumb_Down",
            "Pinch up/down": "Pinch" # Handled separately in logic
        }
        
        new_gestures = config.get("gestures", {})
        for action, ui_name in new_gestures.items():
            if ui_name in ui_to_internal:
                self.gesture_map[action] = ui_to_internal[ui_name]
        
        print("Processor config updated successfully.")

    def process_frame(self, result, frame):
        if not result or not result.gestures or not result.handedness or len(result.handedness) == 0:
            self.reset_gesture_states()
            return None
        
        # Hand Preference check
        chosen_hand_idx = -1
        for i in range(len(result.handedness)):
            try:
                det_hand = result.handedness[i][0].category_name
                pref = self.user_hand_preference
                if pref == "Both / No Preference" or det_hand == pref:
                    chosen_hand_idx = i
                    break
            except: continue
                
        if chosen_hand_idx == -1:
            self.reset_gesture_states()
            return None
        
        try:
            h, w, _ = frame.shape
            hand_landmarks = result.hand_landmarks[chosen_hand_idx]
            wrist = hand_landmarks[0]
            middle_mcp = hand_landmarks[9]
            gesture_name = result.gestures[chosen_hand_idx][0].category_name
        except: return None
        
        # Visual indicator
        cv2.circle(frame, (int(wrist.x * w), int(wrist.y * h)), 8, (0, 255, 255), 2)
        
        hand_size = sqrt((middle_mcp.x - wrist.x)**2 + (middle_mcp.y - wrist.y)**2)
        scale_factor = max(0.5, min(0.15 / max(hand_size, 0.1), 3.0)) 
        gap_threshold = self.base_gap_threshold / scale_factor
        vol_sens = self.base_volume_sensitivity / scale_factor

        # Gesture Execution Logic ----------------
        # 1. System Toggle
        if gesture_name == self.gesture_map.get("System Toggle"):
            if self.toggle_cooldown.ready():
                self.isSystemOn = not self.isSystemOn
                if not self.isSystemOn: async_typer("`")
                return "System Started" if self.isSystemOn else "System Stopped"
            return None
        
        if not self.isSystemOn: return None

        # 2. Mute Toggle
        if gesture_name == self.gesture_map.get("Mute Toggle"):
            if self.toggle_cooldown.ready():
                self.isMuted = not self.isMuted
                async_typer("m")
                return "Muted" if self.isMuted else "Unmuted"
        
        # 3. Play/Pause
        elif gesture_name == self.gesture_map.get("Play/Pause"):
            if self.toggle_cooldown.ready():
                async_typer("space")
                return "Play/Pause"
        
        # 4. Seeking
        elif gesture_name == self.gesture_map.get("Seek forward"):
            if self.seeker_cooldown.ready():
                async_typer("right")
                return "Seek Forward"
        elif gesture_name == self.gesture_map.get("Seek backward"):
            if self.seeker_cooldown.ready():
                async_typer("left")
                return "Seek Backward"

        # 5. Volume (Pinch) Logic
        if self.gesture_map.get("Volume up/down") == "Pinch":
            thumb_tip, index_tip = hand_landmarks[4], hand_landmarks[8]
            dist = sqrt((thumb_tip.x - index_tip.x)**2 + (thumb_tip.y - index_tip.y)**2)
            f_dist = self.filter(dist)
            curr_pinch = ((thumb_tip.x + index_tip.x) / 2, (thumb_tip.y + index_tip.y) / 2)

            if f_dist <= gap_threshold:
                if self.pinch_start_coords:
                    dy = self.pinch_start_coords[1] - curr_pinch[1]
                    if abs(dy) > vol_sens and self.volume_cooldown.ready():
                        async_typer("up" if dy > 0 else "down")
                        self.pinch_start_coords = curr_pinch 
                        return "Vol Up" if dy > 0 else "Vol Down"
                else:
                    self.pinch_start_coords = curr_pinch
                cv2.circle(frame, (int(curr_pinch[0]*w), int(curr_pinch[1]*h)), 5, (0, 255, 255), -1)
            else:
                self.pinch_start_coords = None

        return None

    def reset_gesture_states(self):
        self.pinch_start_coords = None