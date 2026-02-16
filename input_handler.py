import queue
import requests
import xml.etree.ElementTree as ET
from threading import Thread

# VLC Configuration
VLC_IP = "localhost"        # Change to 127.0.0.1 for raspberry Pi if not working.
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
    
def get_volume():
    """Fetches the current vlc volume from status.xml"""

    url = f"http://{VLC_IP}:{VLC_PORT}/requests/status.xml"
    try:
        response = requests.get(url, auth=VLC_AUTH, timeout=0.2)
        if response.status_code == 200:
            root = ET.fromstring(response.text)
            volume_tag = root.find("volume")
            if volume_tag is not None:
                return int(volume_tag.text)
    except Exception:
        return None
    return None

def input_worker():
    """
    Background thread that sends HTTP requests to VLC.
    - input_worker(): Continuously listens for commands in the input_queue and sends corresponding requests to VLC.
    """

    saved_volume = 256
    while True:
        try:
            key_name = input_queue.get()
            
            # Maps the 'keys' to VLC API commands
            if key_name == "space":
                vlc_request("command=pl_pause")
            elif key_name == "up":
                # Increment volume 
                vlc_request("command=volume&val=+5")
            elif key_name == "down":
                vlc_request("command=volume&val=-5")
            elif key_name == "next":
                # Move now playing to next track
                vlc_request("command=pl_next")
            elif key_name == "prev":
                # Move now playing to previous track
                vlc_request("command=pl_previous")
            elif key_name == "m":
                current_volume = get_volume()
                if current_volume is not None:
                    if current_volume > 0:
                        saved_volume = current_volume
                        vlc_request("command=volume&val=0")
                    else:
                        vlc_request(f"command=volume&val={saved_volume if saved_volume > 0 else 256}")
            elif key_name == "right":
                # Seek forward by 1s for precise controlling
                vlc_request("command=seek&val=+1")
            elif key_name == "left":
                # Seek backward by 1s for precise controlling
                vlc_request("command=seek&val=-1")

            input_queue.task_done()
        except Exception as e:
            print(f"VLC API Worker Error: {e}")

# Start the background worker thread for handling VLC API requests
worker = Thread(target=input_worker, daemon=True)
worker.start()

# Just a intermediate function 
def async_typer(key_name):
    input_queue.put(key_name)