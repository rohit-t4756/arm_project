import cv2 as reader
import mediapipe as mp

# Initialising the camera object
camera = reader.VideoCapture(0)
camera.set(3, 640)
camera.set(4, 480)

# Initialising stuff for Mediapipe
BaseOptions = mp.tasks.BaseOptions
model_path = r"C:\Coding\Projects\arm_project\gesture_recognizer.task"
options = mp.tasks.vision.GestureRecognizerOptions(base_options = BaseOptions(model_asset_path = model_path))
recogniser = mp.tasks.vision.GestureRecognizer.create_from_options(options)

while True:
    _, frame = camera.read()
    if not _:
        continue

    # Converting the frame for mediapipe to work upon.
        # Convert BGR frame to RGB frame
    frame_RGB = reader.cvtColor(frame, reader.COLOR_BGR2RGB)
        # Mediapipe needs the image in a mpImage format.
    mediapipe_img = mp.Image(mp.ImageFormat.SRGB, frame_RGB)

    recogniser_result = recogniser.recognize(mediapipe_img)

    if recogniser_result.gestures:
        # Extract the top gesture category name and score
        top_gesture = recogniser_result.gestures[0][0]
        gesture_name = top_gesture.category_name
        score = top_gesture.score
        
        # Display the result on the original frame
        display_text = f"{gesture_name} ({score})"
        reader.putText(frame, display_text, (50, 50), reader.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, reader.LINE_AA)
    else:
        reader.putText(frame, "No hand detected", (50, 50), reader.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, reader.LINE_AA)

    # 5. Show the original BGR frame (OpenCV expects BGR for imshow)
    reader.imshow("Camera", frame)
    
    if reader.waitKey(1) == ord('q'):
        break

# Cleaning
recogniser.close()
camera.release()
reader.destroyAllWindows()