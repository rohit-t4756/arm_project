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
    with state.lock:
        state.latest_result = result_obj
        state.ai_latency_ms = int((time.time() * 1000) - (timestamp / 1000))
        state.ai_busy = False

def ai_worker(recogniser, camera, processor, monitor):
    while state.is_running:
        loop_start = time.perf_counter()
        
        success, frame = camera.read()
        if not success:
            time.sleep(0.01)
            continue

        capture_timestamp = time.time()

        with state.lock:
            res = state.latest_result
            current_settings = state.settings       # Check for settings update
            
        # Process frame
        action = processor.process_frame(res, frame)
        
        with state.lock:
            if action: state.current_action = action
            state.frame_capture_time = capture_timestamp

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

        monitor.update(loop_start, time.perf_counter())
        time.sleep(0.001)

def main():
    camera = reader.VideoCapture(0)
    camera.set(3, 480) 
    camera.set(4, 320) 

    model_path = "gesture_recognizer.task"
    if not os.path.exists(model_path):
        model_path = os.path.expanduser("~/arm/arm_project/gesture_recognizer.task")
    
    options = mp.tasks.vision.GestureRecognizerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=model_path),
        num_hands=1,
        running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
        result_callback=result_callback
    )
    recogniser = mp.tasks.vision.GestureRecognizer.create_from_options(options)

    # Initialize GUI Wrapper
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
        state.is_running = False
        root.destroy()

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