import tkinter as tk
from PIL import Image, ImageTk
import cv2
from input_handler import async_typer

class GUI:
    def __init__(self, root, processor):
        self.root = root
        self.root.title("Touchless Media Controller (RasPi)")
        self.root.geometry("1200x700")
        self.processor = processor

        # -----------------------------------------------------------------------------------------------------------
        # Theme Configuration ----------------
        self.bg_main = "#1e1e1e"       # Dark background
        self.bg_panel = "#2b2b2b"      # Panel background
        self.fg_text = "#ffffff"       # White text
        self.fg_accent = "#4CAF50"     # Green accent
        self.fg_alert = "#FF5252"      # Red alert
        self.font_header = ("Segoe UI", 12, "bold")
        self.font_body = ("Segoe UI", 10)

        self.root.configure(bg=self.bg_main)

        # Grid configuration ----------------
        # Column config
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)
        self.root.columnconfigure(2, weight=0, minsize=250)
        # Row config
        self.root.rowconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        self.root.rowconfigure(2, weight=0)      # Live Feedback strip
        self.root.rowconfigure(3, weight=0)      # Legend strip


        # Frames configuration ----------------
        # 1. Video Container ----
        self.frame_video = tk.Frame(self.root, bg="black", bd=2, relief="sunken")
        self.frame_video.grid(row=0, column=0, rowspan=2, columnspan=2, sticky="nsew", padx=5, pady=5)

        # Placeholder for the video feed
        self.lbl_video = tk.Label(self.frame_video, bg="black", text="Waiting for Camera...", fg="white")
        self.lbl_video.pack(expand=True, fill="both")


        # 2. Controls ----
        self.frame_controls = tk.Frame(self.root, bg=self.bg_main)
        self.frame_controls.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
        self.frame_controls.configure(background=self.bg_panel)

        # Label (Controls)
        tk.Label(self.frame_controls, text="Controls", bg= self.bg_panel, fg=self.fg_text, font=self.font_header).pack(pady=10, fill='x')
        # Button functions
        def start_system():
            if not self.processor.isSystemOn:
                self.processor.isSystemOn = True
                print("Recognition started.")
                self.processor.last_system_state = "Started"
            self.processor.last_play_state = None
            self.processor.pinch_start_coords = None
        
        def stop_system():
            if self.processor.isSystemOn:
                self.processor.isSystemOn = False
                print("Recognition stopped.")
                async_typer("`")
                self.processor.last_system_state = "Stopped"
            self.processor.last_play_state = None
            self.processor.pinch_start_coords = None
        
        # Buttons
        self.button_container = tk.Frame(self.frame_controls, bg=self.bg_panel)
        self.button_container.pack(fill='x', padx=10)

        self.start_btn = tk.Button(self.button_container, text="Start", bg=self.fg_accent, fg="white", 
                           font=("Segoe UI", 10, "bold"), height=2, borderwidth=0, cursor="hand2", command=start_system)
        self.start_btn.pack(fill='x', pady=5)
        self.stop_btn = tk.Button(self.button_container, text="Stop", bg=self.fg_alert, fg="white", 
                           font=("Segoe UI", 10, "bold"), height=2, borderwidth=0, cursor="hand2", command=stop_system)
        self.stop_btn.pack(fill='both', pady=5)


        # 3. Status ----
        self.frame_status = tk.Frame(self.root, bg=self.bg_main)
        self.frame_status.grid(row=1, column=2, sticky="nsew", padx=5, pady=5)
        self.frame_status.configure(background=self.bg_panel,)

        # Labels (Status, FPS, Latency)
        tk.Label(self.frame_status, text="Metrics", bg= self.bg_panel, fg=self.fg_text, font=self.font_header).pack(fill='x', pady=10)

        # Metrics Grid
        self.metrics_grid = tk.Frame(self.frame_status, bg=self.bg_panel)
        self.metrics_grid.pack(fill="x", padx=15)

        # INITIALIZE METRIC LABELS AS INSTANCE ATTRIBUTES
        self.lbl_fps = self.create_metric_row(self.metrics_grid, "FPS:", 0)
        self.lbl_latency = self.create_metric_row(self.metrics_grid, "End-to-End Latency:", 1)
        self.lbl_sys_status = self.create_metric_row(self.metrics_grid, "Status:", 2)


        # 4. Live Feedback ----
        self.frame_live_feedback = tk.Frame(self.root, borderwidth=3, relief="ridge", bg=self.bg_main)
        self.frame_live_feedback.grid(row=2, column=0, columnspan=3, sticky="nsew")
        self.frame_live_feedback.configure(background=self.bg_panel)

        # Labels (Live Feedback, Detected gesture, Action Performed)
        tk.Label(self.frame_live_feedback, text="Live Feedback", bg=self.bg_panel, fg=self.fg_text, font=self.font_header).pack(side="left", fill='x', padx=10)
        
        # ASSIGN FEEDBACK LABELS TO SELF FOR UPDATING
        self.lbl_detected = tk.Label(self.frame_live_feedback, text="Detected gesture: --", bg=self.bg_panel, fg=self.fg_text, font=self.font_body)
        self.lbl_detected.pack(side="left", expand=True, fill='x', padx=10)
        
        self.lbl_action = tk.Label(self.frame_live_feedback, text="Action performed: --", bg=self.bg_panel, fg=self.fg_text, font=self.font_body)
        self.lbl_action.pack(side="left", expand=True, fill='x', padx=10)


        # 5. Legend ----
        self.frame_legend = tk.Frame(self.root, bg=self.bg_panel, bd=1, relief="flat")
        self.frame_legend.grid(row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=(0, 5))

        legend_data = [
            ("✌ Victory", "Start/Stop"),
            ("✊ Fist", "Play/Pause"),
            ("🤏 Pinch Up/Down", "Volume inc/dec"),
            ("✋ Open Palm", "Mute"),
            ("👍 Thumb Up", "Seek Forward"),
            ("👎 Thumb Down", "Seek Backward")
        ]

        for i, (gesture, desc) in enumerate(legend_data):
            f = tk.Frame(self.frame_legend, bg=self.bg_panel)
            f.pack(side="left", expand=True, fill="x", pady=5)
            tk.Label(f, text=gesture, bg=self.bg_panel, fg=self.fg_text, font=("Segoe UI", 10, "bold")).pack()
            tk.Label(f, text=desc, bg=self.bg_panel, fg="#aaaaaa", font=("Segoe UI", 8)).pack()

    def create_metric_row(self, parent, label_text, row):
        tk.Label(parent, text=label_text, bg=self.bg_panel, fg="#aaaaaa", font=self.font_body).grid(row=row, column=0, sticky="w", pady=2)
        val_lbl = tk.Label(parent, text="--", bg=self.bg_panel, fg=self.fg_text, font=("Consolas", 10))
        val_lbl.grid(row=row, column=1, sticky="e", pady=2)
        parent.columnconfigure(1, weight=1)
        # RETURN THE LABEL OBJECT SO IT CAN BE STORED IN THE CLASS CONSTRUCTOR
        return val_lbl

    # Update Methods for Main Loop ----------------

    def update_video(self, cv_frame):
        # Convert color space
        rgb_frame = cv2.cvtColor(cv_frame, cv2.COLOR_BGR2RGB)
        
        pil_image = Image.fromarray(rgb_frame)
        imgtk = ImageTk.PhotoImage(image=pil_image)
        
        # Update Label
        self.lbl_video.imgtk = imgtk
        self.lbl_video.configure(image=imgtk)

    def update_dashboard(self, fps, latency, gesture_name, action_name, is_system_active):
        # Metrics
        self.lbl_fps.config(text=f"{int(fps)}")
        
        # Latency coloring
        lat_color = self.fg_accent if latency < 200 else self.fg_alert
        self.lbl_latency.config(text=f"{int(latency)} ms", fg=lat_color)
        
        # System Status
        status_text = "ACTIVE" if is_system_active else "OFFLINE"
        status_color = self.fg_accent if is_system_active else self.fg_alert
        self.lbl_sys_status.config(text=status_text, fg=status_color)

        # Live Feedback
        self.lbl_detected.config(text=f"Detected gesture: {gesture_name if gesture_name else '--'}")
        self.lbl_action.config(text=f"Action performed: {action_name if action_name else '--'}")

# -----------------------------------------------------------------------------------------------------------

from gesture_processor_logic import GestureProcessor

if __name__ == "__main__":
    root = tk.Tk()
    processor_temp = GestureProcessor()
    app = GUI(root, processor=processor_temp)
    root.mainloop()