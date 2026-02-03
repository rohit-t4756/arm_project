import cv2 as reader
import mediapipe as mp
import os
import time
from threading import Lock

# Importing our custom modules
from utilities import PerformanceMonitor
from gesture_processor_logic import GestureProcessor

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
        num_hands=1,
        running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
        result_callback=result_callback
    )
    recogniser = mp.tasks.vision.GestureRecognizer.create_from_options(options)

    # Initialize Logic and Monitor
    processor = GestureProcessor()
    monitor = PerformanceMonitor()

    # Main Loop
    while True:
        t_start = time.perf_counter()

        success, frame = camera.read()
        if not success: continue

        frame_RGB = reader.cvtColor(frame, reader.COLOR_BGR2RGB)
        mediapipe_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_RGB)

        # Send frame for recognition
        timestamp_ms = int(time.time() * 1000000)
        recogniser.recognize_async(mediapipe_image, timestamp_ms)

        # Retrieve result safely
        with result_lock:
            current_result = latest_result

        # Call the logic from the external file
        # 'processor' holds all the state (isSystemOn, etc.) internally now
        processor.process_frame(current_result, frame)

        # Performance Monitoring
        t_end = time.perf_counter()
        monitor.update(t_start, t_end)
        fps, total_ms = monitor.get_stats()

        # Overlay
        status_color = (0, 255, 0) if processor.isSystemOn else (0, 255, 255)
        reader.putText(frame, f"LIVE_STREAM | FPS: {fps}", (15, 30), 1, 1.2, status_color, 2)
        reader.putText(frame, f"Latency: {total_ms:.1f}ms", (15, 60), 1, 1.2, (0, 255, 0) if total_ms < 200 else (0, 0, 255), 2)

        # Display
        reader.imshow("Feed", frame)
        if reader.waitKey(1) == ord('q'): break

    # Cleaning
    recogniser.close()
    camera.release()
    reader.destroyAllWindows()

if __name__ == "__main__":
    main()