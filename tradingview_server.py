"""
Flask-сервер для приема вебхуков от TradingView и обработки торговых сигналов.
"""

import threading
from queue import Queue
from flask import Flask, request, jsonify

app = Flask(__name__)

SECRET_KEY = "flytrader_secret_2026"
signal_queue = Queue()
queue_lock = threading.Lock()


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
