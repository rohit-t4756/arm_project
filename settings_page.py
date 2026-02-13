import tkinter as tk

class settings_page(tk.Frame):
    def __init__(self, parent, controller, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.controller = controller
        
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

        self.configure(bg=self.bg_main)
        
        # Page switching buttons
        self.button_frame = tk.Frame(self, bg=self.bg_main)
        self.button_frame.pack(fill="x", padx=8, pady=(8, 0))
        
        # Local import to avoid circular dependency issues at module level
        from main_page import main_page
        
        self.mainpagebtn = tk.Button(self.button_frame, text="Main Page", bg=self.bg_main, bd=1, relief="ridge", fg=self.fg_text,
                                     command=lambda: controller.show_frame(main_page))
        self.mainpagebtn.pack(side="left", padx=0)
        
        self.settingspagebtn = tk.Button(self.button_frame, text="Settings", bg=self.bg_main, bd=1, relief="ridge", fg=self.fg_text,
                                         command=lambda: controller.show_frame(settings_page))
        self.settingspagebtn.pack(side="left", padx=0)

        # Main Layout Container
        self.settings_container = tk.Frame(self, bg=self.bg_main, bd=1, relief=tk.RIDGE)
        self.settings_container.pack(expand=True, fill="both", padx=8, pady=(0, 4))
        
        # Action gesture mapping
        self.action_map_frame = tk.Frame(self.settings_container, bg=self.bg_panel, bd=1, relief="ridge")
        self.action_map_frame.pack(fill="x", padx=8, pady=(8, 4))
        
        self.action_map_frame.columnconfigure(1, weight=1)        # Configure grid columns to balance space

        actions = ["Rest", "System Toggle", "Play/Pause", "Volume up/down", "Mute Toggle", "Seek forward", "Seek backward"]
        gestures = ["Open palm", "Victory", "Pointing up", "Pinch up/down", "Fist", "Thumb up", "Thumb down"]

        self.mappings = {}        # Dictionary to store StringVars for retrieval

        for i, action_text in enumerate(actions):
            # Label
            lbl = tk.Label(
                self.action_map_frame,
                text=action_text,
                bg=self.bg_panel,
                fg=self.fg_text,
                font=self.font_body
            )
            lbl.grid(row=i, column=0, sticky="w", padx=(10, 5), pady=4)

            # Dropdown Logic
            selection = tk.StringVar(self)
            selection.set(gestures[i % len(gestures)])
            self.mappings[action_text] = selection

            dropdown = tk.OptionMenu(self.action_map_frame, selection, *gestures)
            
            # Styling the dropdown button
            dropdown.config(
                bg=self.bg_main, 
                fg=self.fg_text, 
                highlightthickness=0, 
                activebackground=self.fg_accent,
                font=self.font_body,
                relief="flat",
                anchor="w"
            )
            # Styling the dropdown menu list
            dropdown["menu"].config(
                bg=self.bg_main, 
                fg=self.fg_text, 
                font=self.font_body,
                activebackground=self.fg_accent,
                relief="flat"
            )
            
            dropdown.grid(row=i, column=1, sticky="ew", padx=(5, 10), pady=4)

        # Cooldown adjustment frame
        self.cooldown_adjustment_frame = tk.Frame(self.settings_container, bg=self.bg_panel, bd=1, relief="ridge")
        self.cooldown_adjustment_frame.pack(fill="x", padx=8, pady=(4, 8))
        self.cooldown_adjustment_frame.columnconfigure(1, weight=1)

        cooldowns = ["Toggle cooldown", "Volume cooldown", "Seekbar cooldown"]
        self.cooldown_mappings = dict()
        
        for i, cooldown_name in enumerate(cooldowns):
            lbl = tk.Label(
                self.cooldown_adjustment_frame,
                text=cooldown_name,
                bg= self.bg_panel,
                fg=self.fg_text,
                font=self.font_body
            )
            lbl.grid(row=i, column=0, sticky="w", padx=(10, 5), pady=4)
            
            # Slider Logic
            slider = tk.Scale(self.cooldown_adjustment_frame)
            slider.config(
                from_=0.00,
                to=10.00,
                orient="horizontal",
                resolution=0.01,
                bg=self.bg_panel,
                fg=self.fg_text,
                troughcolor=self.bg_main,
                activebackground=self.fg_accent,
                relief="flat",
                font=self.font_body,
                sliderlength=15,
                width=10,
                bd=0,
                highlightthickness=0
            )

            # Set defaults
            if cooldown_name == "Toggle cooldown":
                slider.set(0.6)
            elif cooldown_name == "Volume cooldown":
                slider.set(0.05)
            elif cooldown_name == "Seekbar cooldown":
                slider.set(0.05)

            slider.grid(row=i, column=1, sticky="ew", padx=10, pady=4)
            self.cooldown_mappings[cooldown_name] = slider

        # Other settings frame
        self.other_settings_frame = tk.Frame(self.settings_container, bg=self.bg_panel, bd=1, relief="ridge")
        self.other_settings_frame.pack(fill="x", padx=8, pady=(4, 8))
        self.other_settings_frame.columnconfigure(1, weight=1)

        # Label
        lbl_hand = tk.Label(
            self.other_settings_frame,
            text="Controller Hand Preference",
            bg=self.bg_panel,
            fg=self.fg_text,
            font=self.font_body
        )
        lbl_hand.grid(row=0, column=0, sticky="w", padx=(10, 5), pady=4)

        # Dropdown options
        hand_options = ["Right", "Left", "Both / No Preference"]
        
        # Variable to hold selection
        self.hand_pref_var = tk.StringVar(self)
        self.hand_pref_var.set("Both / No Preference")

        # Create Dropdown
        hand_dropdown = tk.OptionMenu(self.other_settings_frame, self.hand_pref_var, *hand_options)
        
        # Styling the dropdown button
        hand_dropdown.config(
            bg=self.bg_main, 
            fg=self.fg_text, 
            highlightthickness=0, 
            activebackground=self.fg_accent,
            font=self.font_body,
            relief="flat",
            anchor="w"
        )
        # Styling the dropdown menu list
        hand_dropdown["menu"].config(
            bg=self.bg_main, 
            fg=self.fg_text, 
            font=self.font_body,
            activebackground=self.fg_accent,
            relief="flat"
        )
        
        hand_dropdown.grid(row=0, column=1, sticky="ew", padx=(5, 10), pady=4)
        # ---------------------------------------------------------


        # Apply button
        self.apply_btn = tk.Button(
            self, 
            text="Apply", 
            command=self.save_settings,
            bg=self.fg_accent,
            fg="white",
            font=self.font_header,
            activebackground="#3d8b40",
            relief="flat",
            cursor="hand2"
        )
        self.apply_btn.pack(fill="x", padx=16, pady=6)

    def save_settings(self):
        # 1. Extract Gesture Mappings
        gesture_config = {action: var.get() for action, var in self.mappings.items()}
        
        # 2. Extract Cooldown Values
        cooldown_config = {name: slider.get() for name, slider in self.cooldown_mappings.items()}
        
        # 3. Extract Hand Preference
        hand_pref = self.hand_pref_var.get()
        
        # Return as a dictionary
        return {
            "gestures": gesture_config, 
            "cooldowns": cooldown_config,
            "hand_preference": hand_pref
        }