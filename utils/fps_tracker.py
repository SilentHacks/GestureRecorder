from collections import deque

from cv2 import getTickCount, getTickFrequency


class FPSTracker:
    def __init__(self, buffer_len: int = 1):
        self._start_tick = getTickCount()
        self._freq = 1000.0 / getTickFrequency()
        self._difftimes = deque(maxlen=buffer_len)

    def get(self):
        current_tick = getTickCount()
        different_time = (current_tick - self._start_tick) * self._freq
        self._start_tick = current_tick

        self._difftimes.append(different_time)

        fps = 1000.0 / (sum(self._difftimes) / len(self._difftimes))
        fps_rounded = round(fps, 2)

        return fps_rounded
