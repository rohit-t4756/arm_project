"""
Main application entry point for the Touchless Controller.
This script initializes the camera, sets up the gesture recognizer, and starts the main application loop.
It also manages the AI processing thread and updates the GUI with the latest results and performance metrics.
"""

import cv2 as reader
import mediapipe as mp
import os
import time
from threading import Lock, Thread
import tkinter as tk

# Importing custom modules
from utilities import PerformanceMonitor
from app import app
from main_page import main_page
from settings_page import settings_page

class SharedState:
    """
    Shared state object to manage data between the AI worker thread and the main GUI thread.
    Includes:
    - latest_result: The most recent gesture recognition result from the AI.
    - current_action: The current action determined by the processor based on the latest result.
    - lock: A threading lock to ensure thread-safe access to shared variables.
    - is_running: A flag to control the main loop and allow for graceful shutdown.
    - ai_busy: A flag to indicate if the AI is currently processing a frame, used for throttling.
    - ai_latency_ms: Stores the latency of the AI processing for the latest frame.
    - frame_capture_time: Timestamp of when the current frame was captured, used for total latency calculation.
    - settings: A variable to track the current settings from the UI, allowing the AI worker to react to changes in configuration.
    """
    def __init__(self):
        self.latest_result = None
        self.current_action = "Idle"
        self.lock = Lock()
        self.is_running = True
        
        self.ai_busy = False 
        self.ai_latency_ms = 0
        self.frame_capture_time = 0 
        
        self.settings = None        # State variable for settings tracking
    
state = SharedState()

def result_callback(result_obj, inp_img, timestamp):
    """
    Callback function that is called by the MediaPipe recognizer when a new result is available.
    It updates the shared state with the latest result and calculates the AI processing latency.
    Parameters:
        - result_obj: The result object returned by the MediaPipe recognizer, containing gesture recognition results
        - inp_img: The input image that was processed (not used in this callback but can be useful for debugging or future features)
        - timestamp: The timestamp (in microseconds) when the recognizer started processing the frame, used to calculate latency
    Returns:
        - None
    """
    with state.lock:
        state.latest_result = result_obj
        state.ai_latency_ms = int((time.time() * 1000) - (timestamp / 1000))
        state.ai_busy = False

def ai_worker(recogniser, camera, processor, monitor):
    """
    Worker thread function that continuously captures frames from the camera, processes them with the gesture recognizer, and updates the shared state with results and performance metrics.
    Parameters:
        - recogniser: The MediaPipe gesture recognizer instance used to process frames
        - camera: The OpenCV VideoCapture object used to capture frames from the webcam
        - processor: The processor object that takes recognition results and determines the current action
        - monitor: The PerformanceMonitor instance used to track and calculate FPS and other performance metrics
    Returns:
        - None
    """

    while state.is_running:
        loop_start = time.perf_counter()
        
        success, frame = camera.read()      
        if not success:         # If frame capture fails, skip processing and try again
            time.sleep(0.01)
            continue

        capture_timestamp = time.time()

        with state.lock:        # Safely read the latest result and settings for processing
            res = state.latest_result
            current_settings = state.settings
            
        # Process frame
        action = processor.process_frame(res, frame)
        
        with state.lock:
            if action: state.current_action = action
            state.frame_capture_time = capture_timestamp

        # Display the frame (for debugging purposes, can be removed in final version)
        reader.imshow("Touchless Controller Feed", frame)
        if reader.waitKey(1) & 0xFF == ord('q'):
            state.is_running = False
            break

        # AI Throttling
        can_send_to_ai = False
        with state.lock:
            if not state.ai_busy:
                state.ai_busy = True
                can_send_to_ai = True

        if can_send_to_ai:
            frame_RGB = reader.cvtColor(frame, reader.COLOR_BGR2RGB)
            mediapipe_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_RGB)
            current_us = int(capture_timestamp * 1000000) 
            recogniser.recognize_async(mediapipe_image, current_us)

        # Update performance monitor with the time taken for this loop iteration
        monitor.update(loop_start, time.perf_counter())
        time.sleep(0.001)

def main():
    """
    Main function that initializes the camera, gesture recognizer, and GUI, and starts the main application loop.
    It also starts the AI worker thread that handles frame processing and gesture recognition in the background.
    """

    # Initialize camera
    camera = reader.VideoCapture(0)
    camera.set(3, 480) 
    camera.set(4, 320) 

    model_path = "gesture_recognizer.task"
    if not os.path.exists(model_path):
        model_path = os.path.expanduser("~/arm/arm_project/gesture_recognizer.task")
    
    # Initialize MediaPipe Gesture Recognizer with options
    options = mp.tasks.vision.GestureRecognizerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=model_path),
        num_hands=4,
        running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
        result_callback=result_callback
    )
    recogniser = mp.tasks.vision.GestureRecognizer.create_from_options(options)

    # Initialize the main application GUI
    root = app()
    processor = root.processor
    monitor = PerformanceMonitor()
    
    # Store initial settings
    state.settings = root.get_settings()
    processor.update_config(state.settings)
    
    # Start AI thread
    worker_thread = Thread(target=ai_worker, args=(recogniser, camera, processor, monitor), daemon=True)
    worker_thread.start()

    def update_gui():
        """
        Function to update the GUI with the latest results and performance metrics.
        It checks if the application is still running, updates the dashboard with the latest FPS, AI latency, total latency, recognized gesture, and current action. 
        It also checks for any changes in settings from the UI and updates the processor configuration accordingly.
        """
        if not state.is_running:
            root.destroy()
            return

        # If settings change then call new changes from UI
        try:
            current_ui_settings = root.get_settings()
            if current_ui_settings != state.settings:
                with state.lock:
                    state.settings = current_ui_settings
                processor.update_config(current_ui_settings)
        except Exception as e:
            pass


        # Dasboard Updates -------------------
        with state.lock:
            result = state.latest_result
            action = state.current_action
            ai_lat = state.ai_latency_ms
            capture_t = state.frame_capture_time

        total_latency = int((time.time() - capture_t) * 1000) if capture_t > 0 else 0
        gesture_name = "--"
        if result and result.gestures and len(result.gestures) > 0:
            gesture_name = result.gestures[0][0].category_name

        fps, _ = monitor.get_stats()
        
        if main_page in root.frames:
            root.frames[main_page].update_dashboard(
                fps=fps, 
                ai_latency=ai_lat, 
                total_latency=total_latency,
                gesture_name=gesture_name, 
                action_name=action, 
                is_system_active=processor.isSystemOn
            )

        root.after(100, update_gui)

    def on_closing():
        """  
        Function to handle the window closing event. 
        It sets the running flag to False to signal the AI worker thread to stop, and then destroys the main application window.
        """
        state.is_running = False
        root.destroy()

    # Set the window close protocol to ensure a error-free shutdown
    root.protocol("WM_DELETE_WINDOW", on_closing)
    update_gui()
    root.mainloop()

    # Cleanup
    state.is_running = False
    recogniser.close()
    camera.release()
    reader.destroyAllWindows()

if __name__ == "__main__":
    main()