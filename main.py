import cv2 as reader
import mediapipe as mp
import os
import time
from threading import Lock, Thread
import tkinter as tk

# Importing our custom modules
from utilities import PerformanceMonitor
from gesture_processor_logic import GestureProcessor
from gui import GUI

# Thread safe storage
class SharedState:
    def __init__(self):
        self.latest_result = None
        self.latest_frame = None
        self.current_action = "Idle"
        self.lock = Lock()
        self.is_running = True
        self.last_timestamp_ms = 0
        
        # --- THE FIX: The Busy Flag ---
        self.ai_busy = False 
        self.ai_latency_ms = 0
        self.frame_start_time = 0
    
state = SharedState()

def result_callback(result_obj, inp_img, timestamp):
    with state.lock:
        state.latest_result = result_obj
        # Calculate how long the AI actually took to process this specific frame
        state.ai_latency_ms = int((time.time() * 1000) - (timestamp / 1000))
        # Unlock the gate: AI is ready for a new frame
        state.ai_busy = False

def ai_worker(recogniser, camera, processor, monitor):
    """Background thread to handle camera and AI processing."""
    while state.is_running:
        loop_start = time.perf_counter()
        
        success, frame = camera.read()
        if not success:
            continue

        # 1. Retrieve AI results
        with state.lock:
            res = state.latest_result
        
        # 2. Run Logic and Draw directly on the OpenCV frame
        action = processor.process_frame(res, frame)
        
        # --- DIAGNOSTIC: Use Native OpenCV for video instead of Tkinter/Pillow ---
        reader.imshow("Native High-Speed Feed", frame)
        if reader.waitKey(1) & 0xFF == ord('q'):
            state.is_running = False
            break

        # 3. AI Gate: Only send to MediaPipe if it's not currently busy
        can_send_to_ai = False
        with state.lock:
            if not state.ai_busy:
                state.ai_busy = True
                can_send_to_ai = True

        if can_send_to_ai:
            frame_RGB = reader.cvtColor(frame, reader.COLOR_BGR2RGB)
            mediapipe_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_RGB)

            # Use microseconds for MediaPipe timestamp
            current_us = int(time.time() * 1000000)
            recogniser.recognize_async(mediapipe_image, current_us)

        # Performance Monitoring
        monitor.update(loop_start, time.perf_counter())
        
        with state.lock:
            if action: state.current_action = action
            # We no longer store latest_frame for GUI since we use imshow here

        time.sleep(0.001)

def main():
    camera = reader.VideoCapture(0)
    # 320x240 is the standard for Pi high-speed CV
    camera.set(reader.CAP_PROP_FRAME_WIDTH, 320)
    camera.set(reader.CAP_PROP_FRAME_HEIGHT, 240)

    model_path = "gesture_recognizer.task"
    if not os.path.exists(model_path):
        model_path = os.path.expanduser("~/arm/arm_project/gesture_recognizer.task")
    
    options = mp.tasks.vision.GestureRecognizerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=model_path),
        num_hands=2, 
        running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
        result_callback=result_callback
    )
    recogniser = mp.tasks.vision.GestureRecognizer.create_from_options(options)

    processor = GestureProcessor()
    monitor = PerformanceMonitor()
    
    # Initialize Tkinter
    root = tk.Tk()
    app = GUI(root, processor)

    # Start AI Thread
    worker_thread = Thread(target=ai_worker, args=(recogniser, camera, processor, monitor), daemon=True)
    worker_thread.start()

    def update_gui():
        """Update only the text dashboard. No Pillow/Image conversions."""
        with state.lock:
            result = state.latest_result
            action = state.current_action
            ai_lat = state.ai_latency_ms

        # Metrics update
        gesture_name = "--"
        if result and result.gestures and len(result.gestures) > 0:
            gesture_name = result.gestures[0][0].category_name

        fps, _ = monitor.get_stats()
        
        # We skip app.update_video(frame) entirely!
        app.update_dashboard(fps, ai_lat, gesture_name, action, processor.isSystemOn)

        root.after(100, update_gui) # Slow down GUI update to save CPU

    update_gui()
    root.mainloop()

    state.is_running = False
    recogniser.close()
    camera.release()
    reader.destroyAllWindows()

if __name__ == "__main__":
    main()