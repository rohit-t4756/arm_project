import cv2 as reader
import mediapipe as mp
import os
import time
from threading import Lock
import tkinter as tk

# Importing our custom modules
from utilities import PerformanceMonitor
from gesture_processor_logic import GestureProcessor
from gui import GUI

# Result storage for the async callback
latest_result = None
result_lock = Lock()

def result_callback(result_obj, inp_img, timestamp):
    global latest_result
    with result_lock:
        latest_result = result_obj

def main():
    # Initialising system
    camera = reader.VideoCapture(0)
    camera.set(3, 640)
    camera.set(4, 480)

    # Setup MediaPipe
    BaseOptions = mp.tasks.BaseOptions
    model_path = "gesture_recognizer.task"
    if not os.path.exists(model_path):
        model_path = os.path.expanduser("~/arm/arm_project/gesture_recognizer.task")
    
    options = mp.tasks.vision.GestureRecognizerOptions(
        base_options=BaseOptions(model_asset_path=model_path),
        num_hands=12,
        running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
        result_callback=result_callback
    )
    recogniser = mp.tasks.vision.GestureRecognizer.create_from_options(options)

    # Initialize Logic and GUI
    processor = GestureProcessor()
    monitor = PerformanceMonitor()

    root = tk.Tk()
    app = GUI(root, processor)

    # Main Loop
    def loop():
        t_start = time.perf_counter()

        success, frame = camera.read()
        if not success: 
            root.after(10, loop)
            return

        frame_RGB = reader.cvtColor(frame, reader.COLOR_BGR2RGB)
        mediapipe_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_RGB)

        # Send frame for recognition
        timestamp_ms = int(time.time() * 1000000)
        recogniser.recognize_async(mediapipe_image, timestamp_ms)

        # Retrieve result safely
        with result_lock:
            current_result = latest_result

        # Call the logic from the external file
        action_text = processor.process_frame(current_result, frame)

        # Performance Monitoring
        t_end = time.perf_counter()
        monitor.update(t_start, t_end)
        fps, total_ms = monitor.get_stats()

        # Extract the gesture name
        gesture_name = "None"
        if current_result and current_result.gestures:
            gesture_name = current_result.gestures[0][0].category_name

        # app updates
        app.update_video(frame)
        app.update_dashboard(
            fps= fps,
            latency= total_ms,
            gesture_name= gesture_name,
            action_name= action_text if processor.isSystemOn else "Idle",
            is_system_active= processor.isSystemOn
        )

        # Schedule the next iteration (10ms delay)
        root.after(10, loop)

    # Start the loop
    loop()
    
    # Start the main window.
    root.mainloop()

    # Cleaning
    recogniser.close()
    camera.release()

if __name__ == "__main__":
    main()