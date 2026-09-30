from __future__ import annotations

from collections import deque
from datetime import datetime


class Historian:
    def __init__(self, max_points: int = 60, max_events: int = 200) -> None:
        self.level_history = deque(maxlen=max_points)
        self.events = deque(maxlen=max_events)
        self._last_event = None

    def add_level(self, value: float) -> None:
        self.level_history.append(float(value))

    def log(self, message: str, deduplicate: bool = True) -> None:
        if deduplicate and message == self._last_event:
            return

        timestamp = datetime.now().strftime("%H:%M:%S")
        self.events.appendleft(f"{timestamp}  {message}")
        self._last_event = message
