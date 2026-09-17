"""
Потокобезопасный синглтон для хранения текущего состояния симуляции (свечи, сделки, события, метрики).
"""

import threading
import time
from collections import deque

_lock = threading.Lock()
_state = {
    "step": 0,
    "total_steps": 2000,
    "price": 0.0,
    "balance": 100.0,
    "position": 0.0,
    "equity": 100.0,
    "pnl_pct": 0.0,
    "dopamine": 0.2,
    "rpe": 0.0,
    "action": "HOLD",
    "confidence": 0.0,
    "fly_mode": "A",
    "mode": "live",
    "running": False,
    "candles": deque(maxlen=200),
    "trades": deque(maxlen=50),
    "events": deque(maxlen=20),
}


def get_state():
    with _lock:
        return dict(_state)


def update(**kwargs):
    with _lock:
        _state.update(kwargs)


def push_candle(c):
    with _lock:
        _state["candles"].append(c)


def push_trade(t):
    with _lock:
        _state["trades"].append(t)


def push_event(evt_type, data=None):
    with _lock:
        _state["events"].append({
            "type": evt_type,
            "data": data or {},
            "t": time.time()
        })
