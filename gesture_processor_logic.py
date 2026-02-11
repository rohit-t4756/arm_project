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
        self.base_volume_sensitivity = 0.08
        self.isPlaying = False
        self.isSystemOn = False
        self.isMuted = False
        self.user_hand_preference = "left" 
        
        # Cooldowns
        self.toggle_cooldown = GestureCooldown(limit=1.0)
        self.volume_cooldown = GestureCooldown(limit=0.1)
        self.seeker_cooldown = GestureCooldown(limit=0.5)

        # OneEuroFilter
        self.config = {
            'freq': 30,      
            'mincutoff': 1.5,
            'beta': 5,      
            'dcutoff': 1.0    
        }
        self.filter = OneEuroFilter(**self.config)

    def process_frame(self, result, frame):
        # 1. Trivial checks
        if not result or not result.gestures or not result.handedness or len(result.handedness) == 0:
            self.reset_gesture_states()
            return None
        
        # 2. Hand Preference Check 
        chosen_hand_idx = -1
        for i in range(len(result.handedness)):
            try:
                detected_handedness = result.handedness[i][0].category_name.lower()
                if detected_handedness == self.user_hand_preference.lower():
                    chosen_hand_idx = i
                    break
            except (IndexError, AttributeError):
                continue
                
        if chosen_hand_idx == -1:
            self.reset_gesture_states()
            return None
        
        # 3. Data Extraction
        try:
            h, w, _ = frame.shape
            hand_landmarks = result.hand_landmarks[chosen_hand_idx]
            wrist = hand_landmarks[0]
            middle_mcp = hand_landmarks[9]
            gesture_name = result.gestures[chosen_hand_idx][0].category_name
        except (IndexError, AttributeError):
            return None
        
        # Visual Feedback
        cv2.circle(frame, (int(wrist.x * w), int(wrist.y * h)), 8, (0, 255, 255), 2)
        
        # 4. Distance Scaling (No numpy for better Pi stability)
        dist_sq = (middle_mcp.x - wrist.x)**2 + (middle_mcp.y - wrist.y)**2
        hand_size = sqrt(dist_sq)
        
        raw_scale = 0.15 / max(hand_size, 0.1)
        # Replacing np.clip with pure Python min/max
        scale_factor = max(0.5, min(raw_scale, 3.0)) 

        gap_threshold = self.base_gap_threshold / scale_factor
        volume_sensitivity = self.base_volume_sensitivity / scale_factor

        # --- Gesture Execution Logic ---
        
        # System Toggle
        if gesture_name == 'Victory':
            if self.toggle_cooldown.ready():
                self.isSystemOn = not self.isSystemOn
                if not self.isSystemOn: 
                    async_typer("`")
                print("System Started" if self.isSystemOn else "System Stopped")
                return "System Started" if self.isSystemOn else "System Stopped"
            return None
        
        if not self.isSystemOn:
            return None

        # Actions (only if system is On)
        if gesture_name == 'Closed_Fist':
            if self.toggle_cooldown.ready():
                self.isMuted = not self.isMuted
                async_typer("m")
                print("Mute Toggled")
                return "Muted" if self.isMuted else "Unmuted"
        
        elif gesture_name == 'Pointing_Up':
            if self.toggle_cooldown.ready():
                self.isPlaying = not self.isPlaying
                async_typer("space")
                print("Play/Pause Toggled")
                return "Video Toggled"

        elif gesture_name == 'Thumb_Up':
            if self.seeker_cooldown.ready():
                async_typer("right")
                print("Seeked Forward")
                return "Seek Forward"
        
        elif gesture_name == 'Thumb_Down':
            if self.seeker_cooldown.ready():
                async_typer("left")
                print("Seeked Backward")
                return "Seek Backward"

        # Volume (Pinch) Logic
        thumb_tip = hand_landmarks[4]
        index_tip = hand_landmarks[8]
        dist = sqrt((thumb_tip.x - index_tip.x)**2 + (thumb_tip.y - index_tip.y)**2)
        f_dist = self.filter(dist, timestamp=int(time.time() * 1000000))
        curr_pinch = ((thumb_tip.x + index_tip.x) / 2, (thumb_tip.y + index_tip.y) / 2)

        if f_dist <= gap_threshold:
            if self.pinch_start_coords is None:
                self.pinch_start_coords = curr_pinch
            else:
                dy = self.pinch_start_coords[1] - curr_pinch[1]
                if abs(dy) > volume_sensitivity and self.volume_cooldown.ready():
                    async_typer("up" if dy > 0 else "down")
                    self.pinch_start_coords = curr_pinch 
                    print("Vol Up" if dy > 0 else "Vol Down")
                    return "Vol Up" if dy > 0 else "Vol Down"
            
            cv_pos = (int(curr_pinch[0] * w), int(curr_pinch[1] * h))
            cv2.circle(frame, cv_pos, 5, (0, 255, 255), -1)
        else:
            self.pinch_start_coords = None

        return None

    def reset_gesture_states(self):
        self.pinch_start_coords = None