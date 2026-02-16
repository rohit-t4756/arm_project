**Touchless Human Computer Interface (HCI) for Media Control**

**Overview**

This project is a high-performance, touchless Human-Computer Interface (HCI) specifically designed for the ARM-based Raspberry Pi 5. It allows users to control VLC Media Player through hand gestures captured via a standard USB webcam. By utilizing Google's MediaPipe framework and OpenCV, the system translates spatial hand coordinates into media commands with minimal latency.

**Key Features**

- **Real-time Hand Gesture Recognition**: Support for complex gestures including victory signs, pointing, fist clenching, and dynamic pinching.
- **Multidimensional Pinch Control**: A quadrant-based logic system that differentiates between vertical movement for volume control and horizontal movement for seeking.
- **Performance Dashboard**: A custom Tkinter GUI providing live metrics on Engine FPS, AI Inference Latency, and system status.
- **VLC Web API Integration**: Background control of VLC using HTTP requests, ensuring commands are executed even when the player is minimized.
- **Hardware Optimization**: Deeply tuned for ARM architecture to achieve desktop-level responsiveness on a single-board computer.

**Hardware Requirements**

- Raspberry Pi 5 4GB(8GB recommended)
- Raspberry Pi Active Cooler (Required for sustained AI inference)
- USB Webcam (720p 30fps minimum)
- Display Monitor with microHDMI connection
- Wired Keyboard and Mouse

**Technical Optimizations**

To achieve an end-to-end latency of 90-110ms on embedded hardware, the following optimizations were implemented:
Busy Flag Synchronization: A non-blocking gate system that discards overflow camera frames to prevent buffer bloat and ensure the AI always processes the freshest data.
XNNPACK Delegation: MediaPipe is configured to use XNNPACK kernels, optimizing floating-point math for ARM Neon instructions.
OneEuroFilter: An adaptive low-pass filter used to eliminate coordinate jitter while maintaining high responsiveness during rapid movements.
Asynchronous AI Worker: The inference engine runs in a dedicated thread separate from the GUI and camera capture to maximize multi-core CPU utilization.
Native Rendering: Video feed is rendered through native OpenCV windows to bypass the processing overhead associated with Python-based image conversion.

**Installation and Setup**

**1. Prerequisites**

Ensure your Raspberry Pi is running a 64-bit OS and create a venv using python3.10.x then, install the necessary dependencies:

`pip install -r requirements.txt`


**2. VLC Configuration**

The system communicates with VLC via its web interface.
1. Open VLC Media Player.
2. Go to Tools -> Preferences -> All.
3. Navigate to Interface -> Main interfaces and check "Web".
4. Under Interface -> Main interfaces -> Lua, set the password to "raspberry".
5. Restart VLC.

**3. Model Preparation**

Place your trained gesture_recognizer.task file in the project root directory. If you need to train a custom model, use the provided gesture_recognizer_trainer.py script.

**Usage**

Enter the venv using:
`source venv_folder_name/bin/activate` (on Linux/ Raspberry Pi OS)

`.\venv_folder_name\Scripts\Activate.ps1` (on Windows)

Check:
`python --version`    - This should print python 3.10.x.

Run the main execution loop:
`python3.10 main.py`

Use the GUI to enable the system and monitor real-time performance.

**Gesture Guide**
1. Victory: Toggle System Power
2. Pointing Up: Play/Pause Video
3. Pinch Vertical: Volume Up/Down
4. Pinch Horizontal: Seek Forward/Backward
5. Fist: Mute Toggle
6. Thub Up: Next Track
7. Thumb Down: Previous Track
8. Open Palm: System Rest / Idle

**Author**

Rohit S. Thorat
Indian Institute of Information Technology Pune
