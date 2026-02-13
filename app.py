import tkinter as tk

# Importing custom modules
from settings_page import settings_page
from main_page import main_page
from gesture_processor_logic import GestureProcessor

class app(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.title("Controller")
        self.geometry("320x675")        
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
        """Raises the selected frame to the top."""
        frame = self.frames[cont]
        frame.tkraise()
    
    def get_settings(self):
        """Correctly calls save_settings on the INSTANCE of settings_page."""
        settings_instance = self.frames[self.settingsPageClass]
        return settings_instance.save_settings()

if __name__ == "__main__":
    hola = app()
    hola.mainloop()