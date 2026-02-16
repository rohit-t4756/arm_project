"""
The GestureProcessor class encapsulates the core logic for interpreting hand gestures and mapping them to media control actions. 
It processes the gesture recognition results, applies user preferences and cooldowns, and executes corresponding media commands through the input_handler.py.
"""

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
        self.base_volume_sensitivity = 0.5
        self.isSystemOn = False
        self.isMuted = False
        
        # Default Settings
        self.user_hand_preference = "Left"
        
        # Default gesture mappings (can be overridden by user)
        self.gesture_map = {
            "System Toggle": "Victory",
            "Play/Pause": "Pointing_Up",
            "Mute Toggle": "Closed_Fist",
            "Seek forward/backward": "Pinch left/right",
            "Next Track": "Thumb_Up",
            "Previous Track": "Thumb_Down",
            'Volume up/down': "Pinch up/down",
            "Rest": "Open_Palm"
        }
        
        # Cooldown timers for different actions to prevent rapid triggering
        self.toggle_cooldown = GestureCooldown(limit=0.6)
        self.pinch_cooldown = GestureCooldown(limit=0.01)
        self.seeker_cooldown = GestureCooldown(limit=0.05)
        self.measurement_cooldown = GestureCooldown(limit=0.1)

        # One Euro Filters for smoothing pinch distance and coordinates
        self.filter_dist = OneEuroFilter(freq=30, mincutoff=1.5, beta=5, dcutoff=1.0)
        self.filter_x = OneEuroFilter(freq=30, mincutoff=1.0, beta=0.5, dcutoff=1.0)
        self.filter_y = OneEuroFilter(freq=30, mincutoff=1.0, beta=0.5, dcutoff=1.0)

    def update_config(self, config):
        """
        Updates internal variables based on a settings dictionary.
        Expected config format:
        {
            "hand_preference": "Left" / "Right" / "Both / No Preference",
            "cooldowns": {
                "Toggle cooldown": 0.6,
                "Volume cooldown": 0.01,
                "Seekbar cooldown": 0.05
            },
            "gestures": {
                "System Toggle": "Victory",
                "Play/Pause": "Pointing up",
                ...
            }
        }
        Output:
            Prints the updated configuration for verification.
        """
        self.user_hand_preference = config.get("hand_preference", "Left")
        
        cooldowns = config.get("cooldowns", {})
        if "Toggle cooldown" in cooldowns:
            self.toggle_cooldown.limit = cooldowns["Toggle cooldown"]
        if "Volume cooldown" in cooldowns:
            self.pinch_cooldown.limit = cooldowns["Volume cooldown"]
        if "Seekbar cooldown" in cooldowns:
            self.seeker_cooldown.limit = cooldowns["Seekbar cooldown"]
            
        ui_to_internal = {
            "Open palm": "Open_Palm",
            "Victory": "Victory",
            "Pointing up": "Pointing_Up",
            "Fist": "Closed_Fist",
            "Thumb up": "Thumb_Up",
            "Thumb down": "Thumb_Down",
            "Pinch up/down": "Pinch up/down",
            "Pinch left/right": "Pinch left/right"
        }
        
        new_gestures = config.get("gestures", {})
        for action, ui_name in new_gestures.items():
            if ui_name in ui_to_internal:
                self.gesture_map[action] = ui_to_internal[ui_name]
        
        print(f"Processor config updated successfully: {config}")

    def process_frame(self, result, frame):
        """
        Processes the gesture recognition results for a single video frame and executes corresponding media control actions based on user preferences and cooldowns.
        Input:
            - result: The output from the gesture recognition model, containing detected gestures, hand landmarks, and handedness information.
            - frame: The current video frame (as a NumPy array) for visual feedback and gesture processing.
        Output:
            - A string indicating the executed action (e.g., "Play/Pause", "Volume Up") or None if no action was taken to be shown in the application's main page.
        """

        if not result or not result.gestures or not result.handedness or len(result.handedness) == 0:
            self.reset_gesture_states()
            return None
        
        # Hand Preference check: Determine which hand's gestures to prioritize based on user settings and detected handedness
        chosen_hand_idx = -1
        for i in range(len(result.handedness)):
            try:
                detected_hand = result.handedness[i][0].category_name
                preference = self.user_hand_preference
                if preference == "Both / No Preference" or detected_hand == preference:
                    chosen_hand_idx = i
                    break
            except: continue
                
        if chosen_hand_idx == -1:
            self.reset_gesture_states()
            return None
        
        # Extract necessary landmarks and gesture information for the chosen hand, with error handling to ensure robustness against incomplete data.
        try:
            h, w, _ = frame.shape
            hand_landmarks = result.hand_landmarks[chosen_hand_idx]
            wrist = hand_landmarks[0]
            middle_mcp = hand_landmarks[9]
            gesture_name = result.gestures[chosen_hand_idx][0].category_name
        except: return None
        
        # Debug Visuals: Draw wrist point and hand size circle for visual feedback on the video feed
        cv2.circle(frame, (int(wrist.x * w), int(wrist.y * h)), 8, (0, 255, 255), 2)
        

        # Gesture Execution Logic ----------------
        hand_size = sqrt((middle_mcp.x - wrist.x)**2 + (middle_mcp.y - wrist.y)**2)
        scale_factor = max(0.5, min(0.10 / max(hand_size, 0.1), 5.0)) 
        gap_threshold = self.base_gap_threshold / scale_factor


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
        
        # 4. Playlist control
        elif gesture_name == self.gesture_map.get("Next Track"):
            if self.toggle_cooldown.ready():
                async_typer("next")
                return "Next track"
        elif gesture_name == self.gesture_map.get("Previous Track"):
            if self.toggle_cooldown.ready():
                async_typer("prev")
                return "Previous track"

        # 5. Pinch Logic
        if self.gesture_map.get("Volume up/down") == "Pinch up/down" or self.gesture_map.get("Seek Forward/Backward") == "Pinch left/right":
            
            thumb_tip, index_tip = hand_landmarks[4], hand_landmarks[8]
            raw_dist = sqrt((thumb_tip.x - index_tip.x)**2 + (thumb_tip.y - index_tip.y)**2)
            finger_dist = self.filter_dist(raw_dist, time.time())
            
            raw_cx = (thumb_tip.x + index_tip.x) / 2
            raw_cy = (thumb_tip.y + index_tip.y) / 2
            curr_pinch_x = self.filter_x(raw_cx, time.time())
            curr_pinch_y = self.filter_y(raw_cy, time.time())
            curr_pinch = (curr_pinch_x, curr_pinch_y)

            if finger_dist <= gap_threshold:
                if self.pinch_start_coords:
                    dy = self.pinch_start_coords[1] - curr_pinch[1]
                    dx = self.pinch_start_coords[0] - curr_pinch[0]
                    distance = sqrt(dx**2 + dy**2)

                    # Debug Visuals: Draw pinch start point, current pinch point, and line connecting them for visual feedback on the video feed
                    start_px = (int(self.pinch_start_coords[0]*w), int(self.pinch_start_coords[1]*h))
                    curr_px = (int(curr_pinch[0]*w), int(curr_pinch[1]*h))
                    cv2.circle(frame, start_px, int(0.07*w), (255, 100, 100), 2)
                    cv2.line(frame, start_px, curr_px, (255, 0, 0), 2)

                    if distance > 0.07 and self.pinch_cooldown.ready():
                        if abs(dx) > abs(dy):                                   # Horizontal movement
                            async_typer("right" if dx > 0 else "left")
                            return "Seek Forward" if dx > 0 else "Seek Backward"
                        else:                                                   # Vertical movement
                            async_typer("up" if dy > 0 else "down")
                            return "Volume Up" if dy > 0 else "Volume Down"
                else:
                    self.pinch_start_coords = curr_pinch
                cv2.circle(frame, (int(curr_pinch[0]*w), int(curr_pinch[1]*h)), 3, (255, 255, 0), -1)
            else:
                self.pinch_start_coords = None

        return None

    def reset_gesture_states(self):
        self.pinch_start_coords = None