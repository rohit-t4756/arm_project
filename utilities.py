import time

class GestureCooldown:
    def __init__(self, limit=1.0):
        self.limit = limit
        self.last_call = 0
    def ready(self):
        now = time.perf_counter()
        if now - self.last_call >= self.limit:
            self.last_call = now
            return True
        return False

class PerformanceMonitor:
    def __init__(self):
        self.inference_times = []
        self.total_latencies = []
        self.fps = 0
        self.last_fps_update = time.time()
        self.frame_count = 0

    def update(self, t_start, t_end):
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
        avg_total = sum(self.total_latencies) / len(self.total_latencies) if self.total_latencies else 0
        return self.fps, avg_total