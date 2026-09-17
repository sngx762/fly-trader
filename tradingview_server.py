"""
Flask-сервер для приема вебхуков от TradingView и обработки торговых сигналов с веб-интерфейсом (Dashboard).
"""

import os
import threading
from queue import Queue
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, template_folder="templates")

SECRET_KEY = os.getenv("FLYTRADER_SECRET", "flytrader_secret_2026")
signal_queue = Queue()
queue_lock = threading.Lock()

# Глобальное состояние для дашборда
system_state = {
    "equity": 100.0,
    "da_level": 0.2,
    "rpe": 0.0,
    "mode": "FlyA (Без наказания)",
    "signals": []
}
state_lock = threading.Lock()


@app.route("/")
def dashboard():
    """Веб-дашборд для визуализации работы торгового агента."""
    return render_template("index.html")


@app.route("/api/status", methods=["GET"])
def api_status():
    """API для получения текущего состояния агента и последних сигналов."""
    with state_lock, queue_lock:
        signals_list = list(signal_queue.queue)
        state_data = system_state.copy()
        state_data["signals"] = signals_list[::-1]
    return jsonify(state_data)


@app.route("/api/update_state", methods=["POST"])
def api_update_state():
    """API для обновления состояния из симулятора."""
    data = request.get_json(silent=True)
    if data:
        with state_lock:
            for k, v in data.items():
                if k in system_state:
                    system_state[k] = v
        return jsonify({"status": "updated"}), 200
    return jsonify({"error": "Invalid data"}), 400


@app.route("/webhook", methods=["POST"])
def webhook():
    """Эндпоинт для приема сигналов вебхуков от TradingView."""
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        client_secret = data.get("secret")
        if client_secret != SECRET_KEY:
            return jsonify({"error": "Forbidden: Invalid secret key"}), 403

        signal = {
            "symbol": data.get("symbol"),
            "action": data.get("action"),
            "price": data.get("price"),
            "timeframe": data.get("timeframe"),
            "strategy": data.get("strategy"),
            "timestamp": data.get("timestamp")
        }

        with queue_lock:
            signal_queue.put(signal)

        return jsonify({"status": "success", "received": signal}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_latest_signal() -> dict:
    """Потокобезопасное извлечение последнего сигнала из очереди."""
    with queue_lock:
        if not signal_queue.empty():
            return signal_queue.get()
    return None


def start_server(host: str = "0.0.0.0", port: int = 5001):
    """Запуск Flask-сервера (предназначен для запуска в отдельном потоке)."""
    app.run(host=host, port=port, debug=False, use_reloader=False)
