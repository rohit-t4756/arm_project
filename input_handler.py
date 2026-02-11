import queue
import requests
from threading import Thread

# VLC Configuration
VLC_IP = "127.0.0.1"
VLC_PORT = "8080"
VLC_PASSWORD = "raspberry"  # Match the password you set in VLC settings
VLC_AUTH = ("", VLC_PASSWORD) # VLC uses an empty username

# Queue to store pending commands
input_queue = queue.Queue()

def vlc_request(command_url):
    """Helper to send the HTTP GET request to VLC."""
    url = f"http://{VLC_IP}:{VLC_PORT}/requests/status.xml?{command_url}"
    try:
        # We use a short timeout to prevent the worker from hanging
        response = requests.get(url, auth=VLC_AUTH, timeout=0.2)
        return response.status_code == 200
    except Exception as e:
        # Silently fail if VLC isn't open yet
        return False

def input_worker():
    """Background thread that sends HTTP requests to VLC."""
    while True:
        try:
            key_name = input_queue.get()
            
            # Map the previous 'keys' to VLC API commands
            if key_name == "space":
                vlc_request("command=pl_pause")
            
            elif key_name == "up":
                # Increment volume (VLC uses 0-512, 256 is 100%)
                vlc_request("command=volume&val=+10") 
                
            elif key_name == "down":
                vlc_request("command=volume&val=-10")
                
            elif key_name == "right":
                # Seek forward 10 seconds
                vlc_request("command=seek&val=+10s")
                
            elif key_name == "left":
                # Seek backward 10 seconds
                vlc_request("command=seek&val=-10s")
                
            elif key_name == "m":
                vlc_request("command=volume&val=0")

            input_queue.task_done()
        except Exception as e:
            print(f"VLC API Worker Error: {e}")

# Start the SINGLE worker thread
worker = Thread(target=input_worker, daemon=True)
worker.start()

def async_typer(key_name):
    """
    Maintains the same function name so you don't have to 
    change 'gesture_logic_processor.py'.
    """
    input_queue.put(key_name)