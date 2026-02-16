"""
Main application file for the gesture control system. This file initializes the GUI, manages page navigation, and integrates the gesture processing logic.
Key components:
- app class: The main application class that sets up the GUI and manages page transitions.
- get_settings method: Retrieves the current settings from the settings page instance.
- Main loop: Initializes the application and starts the main event loop.
"""
import tkinter as tk

# Importing custom modules
from settings_page import settings_page
from main_page import main_page
from gesture_processor_logic import GestureProcessor

class app(tk.Tk):
    def __init__(self, *args, **kwargs):
        """
        Initializes the main application window, sets up the container for pages, and initializes the gesture processor.
        It also creates instances of the main page and settings page, storing them in a dictionary for easy access and navigation using the show_frame method.
        """
        tk.Tk.__init__(self, *args, **kwargs)

        self.title("Controller")
        self.geometry("320x650")        
        self.resizable(False, True)

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        self.processor = GestureProcessor()

        # Storing the class references 
        self.mainPageClass = main_page
        self.settingsPageClass = settings_page

        # Initialize both pages
        for F in (self.mainPageClass, self.settingsPageClass):
            if F == main_page:
                # Main page needs parent, controller (self), and processor
                frame = F(parent=container, controller=self, processor=self.processor)
            else:
                # Settings page only takes parent and controller
                frame = F(parent=container, controller=self)
                
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        
        self.show_frame(main_page)
    
    def show_frame(self, cont):
        """
        Raises the selected frame to the top.
        """
        frame = self.frames[cont]
        frame.tkraise()
    
    def get_settings(self):
        """
        Correctly calls save_settings on the INSTANCE of settings_page.
        """
        settings_instance = self.frames[self.settingsPageClass]
        return settings_instance.save_settings()

if __name__ == "__main__":
    hola = app()
    hola.mainloop()