import queue
import requests
from threading import Thread

# VLC Configuration
VLC_IP = "localhost"        # Change to 127.0.0.1 for raspberry Pi
VLC_PORT = "8080"
VLC_PASSWORD = "raspberry"
VLC_AUTH = ("", VLC_PASSWORD)

# Queue to store pending commands
input_queue = queue.Queue()

def vlc_request(command_url):
    """Helper to send the HTTP GET request to VLC."""
    url = f"http://{VLC_IP}:{VLC_PORT}/requests/status.xml?{command_url}"
    try:
        response = requests.get(url, auth=VLC_AUTH, timeout=0.2)        # Short timeout to prevent the worker from hanging
        return response.status_code == 200
    except Exception as e:          # If VLC isn't open yet.
        return False

def input_worker():
    """Background thread that sends HTTP requests to VLC."""
    while True:
        try:
            key_name = input_queue.get()
            
            # Map the 'keys' to VLC API commands
            if key_name == "space":
                vlc_request("command=pl_pause")
            
            elif key_name == "up":
                # Increment volume (VLC uses 0-512, 256 is 100%)
                vlc_request("command=volume&val=+1") 
                
            elif key_name == "down":
                vlc_request("command=volume&val=-1")
                
            elif key_name == "right":
                # Seek forward 10 seconds
                vlc_request("command=seek&val=+1s")
                
            elif key_name == "left":
                # Seek backward 10 seconds
                vlc_request("command=seek&val=-1s")
                
            elif key_name == "m":
                vlc_request("command=volume&val=0")

            input_queue.task_done()
        except Exception as e:
            print(f"VLC API Worker Error: {e}")

# Start the SINGLE worker thread
worker = Thread(target=input_worker, daemon=True)
worker.start()

def async_typer(key_name):
    input_queue.put(key_name)