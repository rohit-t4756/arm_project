import time

class GestureCooldown:
    """
    Utility class to manage cooldowns for gestures.
    """
    def __init__(self, limit=1.0):
        self.limit = limit
        self.last_call = 0

    def ready(self):
        """
        Checks if the cooldown period has passed and updates the last call time if it has.
        Returns:
            bool: True if the cooldown period has passed, False otherwise.
        """
        now = time.perf_counter()
        if now - self.last_call >= self.limit:
            self.last_call = now
            return True
        return False

class PerformanceMonitor:
    """
    Utility class to monitor performance metrics like FPS and latency.
    """
    def __init__(self):
        self.inference_times = []
        self.total_latencies = []
        self.fps = 0
        self.last_fps_update = time.time()
        self.frame_count = 0

    def update(self, t_start, t_end):
        """
        Updates the performance metrics based on the start and end times of a processing loop.
        Args:
            t_start (float): The start time of the processing loop.
            t_end (float): The end time of the processing loop.
        
        Returns:
            None
        """
        total_ms = (t_end - t_start) * 1000
        self.total_latencies.append(total_ms)
        
        if len(self.total_latencies) > 30:
            self.total_latencies.pop(0)
            
        self.frame_count += 1
        if time.time() - self.last_fps_update > 1.0:
            self.fps = self.frame_count
            self.frame_count = 0
            self.last_fps_update = time.time()

    def get_stats(self):
        """
        Returns:
            tuple: A tuple containing the current FPS and average latency.
        """
        avg_total = sum(self.total_latencies) / len(self.total_latencies) if self.total_latencies else 0
        return self.fps, avg_total