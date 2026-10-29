"""事件总线：单调整序号 + 增量拉取，规避 WebView 跨线程主动推送的不稳定性。"""
from __future__ import annotations

import threading
from collections import deque
from typing import Any


class EventBus:
    def __init__(self, maxlen: int = 4000) -> None:
        self._lock = threading.RLock()
        self._seq = 0
        self._events: deque[dict[str, Any]] = deque(maxlen=maxlen)

    @property
    def seq(self) -> int:
        with self._lock:
            return self._seq

    def emit(self, etype: str, **payload: Any) -> int:
        with self._lock:
            self._seq += 1
            ev = {"seq": self._seq, "type": etype}
            ev.update(payload)
            self._events.append(ev)
            return self._seq

    def log(self, msg: str, level: str = "info") -> int:
        return self.emit("log", level=level, msg=msg)

    def poll(self, since: int = 0, limit: int = 500) -> dict[str, Any]:
        with self._lock:
            items = [e for e in self._events if e["seq"] > since]
            dropped = False
            if self._events and since and since < self._events[0]["seq"] - 1:
                dropped = True
            total = len(items)
            items = items[:limit]
            return {
                "seq": self._seq,
                "events": items,
                "dropped": dropped,
                "remaining": max(0, total - len(items)),
            }

    def reset(self) -> None:
        with self._lock:
            self._events.clear()
            self._seq = 0


bus = EventBus()
