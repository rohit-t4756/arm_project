import tkinter as tk
from input_handler import async_typer

class main_page(tk.Frame):
    """
    Class representing the main page of the application. It displays system controls, metrics, and provides navigation to the settings page.
    Methods:
    - __init__(parent, controller, processor): Initializes the main page with UI elements for system control and metrics display.
    - create_metric_item(parent, label_text, initial_val): Helper method to create a labeled metric display item.
    - update_dashboard(fps, ai_latency, total_latency, gesture_name, action_name, is_system_active): Updates the dashboard with the latest performance metrics and detected gestures/actions.
    """
    def __init__(self, parent, controller, processor):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.processor = processor

        # Theme Configuration
        self.bg_main = "#121212"       
        self.bg_panel = "#1e1e1e"      
        self.fg_text = "#e0e0e0"       
        self.fg_accent = "#4CAF50"     
        self.fg_alert = "#f44336"      
        self.fg_dim = "#888888"        
        
        self.font_header = ("Segoe UI", 12, "bold")
        self.font_metric_val = ("Consolas", 11, "bold")
        self.font_body = ("Segoe UI", 9)
        self.font_legend_title = ("Segoe UI", 10, "bold")
        self.font_legend_desc = ("Segoe UI", 10)

        self.configure(bg=self.bg_main)

        # Main Layout Container
        self.main_container = tk.Frame(self, bg=self.bg_main, padx=10, pady=10)
        self.main_container.pack(expand=True, fill="both")

        # 1. Header Section 
        self.header_frame = tk.Frame(self.main_container, bg=self.bg_main)
        self.header_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(self.header_frame, text="GESTURE CONTROL", bg=self.bg_main, 
                 fg=self.fg_accent, font=self.font_header).pack(anchor="w")
        tk.Label(self.header_frame, text="VLC Web API Mode", bg=self.bg_main, 
                 fg=self.fg_dim, font=self.font_body).pack(anchor="w")
        
        # Page switching buttons
        self.button_frame = tk.Frame(self.main_container, bg=self.bg_main)
        self.button_frame.pack(fill="x", padx=4, pady=(8, 0))
        
        from settings_page import settings_page
        
        self.mainpagebtn = tk.Button(self.button_frame, text="Main Page", bg=self.bg_panel, bd=1, relief="ridge", fg=self.fg_accent,
                                     command=lambda: controller.show_frame(main_page))
        self.mainpagebtn.pack(side="left", expand=True, fill="x", padx=0)
        
        self.settingspagebtn = tk.Button(self.button_frame, text="Settings", bg=self.bg_main, bd=1, relief="ridge", fg=self.fg_text,
                                          command=lambda: controller.show_frame(settings_page))
        self.settingspagebtn.pack(side="left", expand=True, fill="x", padx=0)

        # 2. System Controls
        self.ctrl_frame = tk.LabelFrame(self.main_container, text=" System Power ", bg=self.bg_main, 
                                        fg=self.fg_dim, font=self.font_body, labelanchor="n", padx=5, pady=5)
        self.ctrl_frame.pack(fill="x", pady=5)

        def start_system():
            self.processor.isSystemOn = True
            self.processor.reset_gesture_states()
            print("System Started")
        
        def stop_system():
            self.processor.isSystemOn = False
            async_typer("`")
            self.processor.reset_gesture_states()
            print("System Stopped")

        self.start_btn = tk.Button(self.ctrl_frame, text="ENABLE SYSTEM", bg=self.fg_accent, fg="white", 
                                   font=("Segoe UI", 9, "bold"), height=1, bd=0, cursor="hand2", command=start_system)
        self.start_btn.pack(fill="x", pady=2)
        
        self.stop_btn = tk.Button(self.ctrl_frame, text="DISABLE SYSTEM", bg=self.fg_alert, fg="white", 
                                  font=("Segoe UI", 9, "bold"), height=1, bd=0, cursor="hand2", command=stop_system)
        self.stop_btn.pack(fill="x", pady=2)

        # 3. Metrics Section
        self.metrics_frame = tk.Frame(self.main_container, bg=self.bg_panel, padx=8, pady=8)
        self.metrics_frame.pack(fill="x", pady=5)

        self.lbl_fps = self.create_metric_item(self.metrics_frame, "Engine FPS", "0")
        self.lbl_ai_latency = self.create_metric_item(self.metrics_frame, "AI Latency", "0 ms")
        self.lbl_total_latency = self.create_metric_item(self.metrics_frame, "Total Latency", "0 ms")
        self.lbl_sys_status = self.create_metric_item(self.metrics_frame, "Status", "OFFLINE")

        # 4. Live Feedback Section
        self.feedback_frame = tk.Frame(self.main_container, bg=self.bg_main)
        self.feedback_frame.pack(fill="x", pady=5)

        tk.Label(self.feedback_frame, text="CURRENT ACTIVITY", bg=self.bg_main, 
                 fg=self.fg_dim, font=self.font_body).pack(anchor="w")
        
        self.lbl_detected = tk.Label(self.feedback_frame, text="Gesture: --", bg=self.bg_main, 
                                     fg=self.fg_text, font=self.font_body)
        self.lbl_detected.pack(anchor="w")
        
        self.lbl_action = tk.Label(self.feedback_frame, text="Action: Idle", bg=self.bg_main, 
                                   fg=self.fg_accent, font=("Segoe UI", 10, "bold"))
        self.lbl_action.pack(anchor="w")

        # 5. Vertical Legend Section
        self.legend_frame = tk.LabelFrame(self.main_container, text=" Gesture Guide ", bg=self.bg_main, 
                                          fg=self.fg_dim, font=self.font_body, labelanchor="n", padx=5, pady=5)
        self.legend_frame.pack(fill="both", expand=True, pady=5)

        # Legend Data
        emojis = {
            "pinch": "\U0001F90F",
            "thumb_up": "\U0001F44D",
            "thumb_down": "\U0001F44E",
            "victory": "\u270C",
            "open_palm": "\u270B",
            "fist": "\u270A",
            "point_up": "\u261D"
        }
        legend_data = [
            (f"{emojis['victory']} Victory", "System On/Off"),
            (f"{emojis['open_palm']} Open Palm", "Rest"),
            (f"{emojis['point_up']} Pointing Up", "Play/Pause"),
            (f"{emojis['thumb_up']} Thumb Up", "Next Track"),
            (f"{emojis['thumb_down']} Thumb Down", "Previous Track"),
            (f"{emojis['fist']} Fist", "Mute Toggle"),
            (f"{emojis['pinch']} Pinch (Vertical)", "Volume Up/Down"),
            (f"{emojis['pinch']} Pinch (Horizontal)", "Seek Forward/Back"),
        ]

        for gesture, desc in legend_data:
            item = tk.Frame(self.legend_frame, bg=self.bg_main)
            item.pack(fill="x", pady=1)
            tk.Label(item, text=gesture, bg=self.bg_main, fg=self.fg_accent, 
                     font=self.font_legend_title).pack(anchor="w", side="left")
            tk.Label(item, text=f" - {desc}", bg=self.bg_main, fg=self.fg_dim, 
                     font=self.font_legend_desc).pack(anchor="w", side="left")

    def create_metric_item(self, parent, label_text, initial_val):
        """
        Helper method to create a labeled metric display item in the dashboard.
        
        :param parent: The parent tkinter widget where this metric item will be placed.
        :param label_text: The text label describing the metric (e.g., "Engine FPS").
        :param initial_val: The initial value to display for the metric (e.g., "0 ms"). This will be updated dynamically as the application runs.
        :return: A reference to the value label widget, which can be updated later with new metric values.
        """
        frame = tk.Frame(parent, bg=self.bg_panel)
        frame.pack(fill="x", pady=1)
        tk.Label(frame, text=label_text, bg=self.bg_panel, fg=self.fg_dim, font=self.font_body).pack(side="left")
        val_lbl = tk.Label(frame, text=initial_val, bg=self.bg_panel, fg=self.fg_text, font=self.font_metric_val)
        val_lbl.pack(side="right")
        return val_lbl

    def update_dashboard(self, fps, ai_latency, total_latency, gesture_name, action_name, is_system_active):
        """
        Updates the text-based components of the GUI.
        This method is called periodically (e.g., every 100 ms) to refresh the displayed performance metrics, detected gestures, and current action status. 
        It also updates the system status indicator based on whether the gesture control system is active or offline.

        :param fps: The current frames per second of the gesture recognition engine.
        :param ai_latency: The latency of the AI processing in milliseconds.
        :param total_latency: The total latency from frame capture to action execution in milliseconds.
        :param gesture_name: The name of the currently detected gesture, if any.
        :param action_name: The name of the current action being performed based on the detected gesture
        :param is_system_active: A boolean indicating whether the gesture control system is currently active (True) or offline (False).
        """
        self.lbl_fps.config(text=f"{int(fps)}")
        
        ai_lat_color = self.fg_accent if ai_latency < 100 else self.fg_alert
        self.lbl_ai_latency.config(text=f"{int(ai_latency)} ms", fg=ai_lat_color)
        
        total_lat_color = self.fg_accent if total_latency < 150 else self.fg_alert
        self.lbl_total_latency.config(text=f"{int(total_latency)} ms", fg=total_lat_color)
        
        status_text = "ACTIVE" if is_system_active else "OFFLINE"
        status_color = self.fg_accent if is_system_active else self.fg_alert
        self.lbl_sys_status.config(text=status_text, fg=status_color)

        self.lbl_detected.config(text=f"Gesture: {gesture_name if gesture_name else '--'}")
        
        action_display = action_name if action_name else "Watching..."
        self.lbl_action.config(text=f"Action: {action_display}")