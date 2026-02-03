from threading import Thread
from pynput.keyboard import Key, Controller

keyboard = Controller()

KEY_MAP = {
    "space": Key.space,
    "up": Key.up,
    "down": Key.down,
    "q": 'q'
}

def async_typer(key_name):
    """
    Uses pynput to press keys safely in a thread.
    """
    def press():
        try:
            target_key = KEY_MAP.get(key_name, key_name)
            keyboard.press(target_key)
            keyboard.release(target_key)
        except Exception as e:
            print(f"Pynput Error: {e}")
            
    Thread(target=press, daemon=True).start()