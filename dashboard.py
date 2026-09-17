"""
Flask Blueprint для 3D дашборда и SSE (Server-Sent Events) эндпоинтов.
"""

import json
import time
from flask import Blueprint, render_template, jsonify, Response
import shared_state

bp = Blueprint("dashboard", __name__)


@bp.route("/")
def index():
    return render_template("dashboard.html")


@bp.route("/api/state")
def api_state():
    s = shared_state.get_state()
    return jsonify({k: s[k] for k in [
        "step", "total_steps", "price", "balance", "position", "equity",
        "pnl_pct", "dopamine", "rpe", "action", "confidence", "fly_mode",
        "mode", "running"
    ]})


@bp.route("/api/candles")
def api_candles():
    return jsonify(list(shared_state.get_state()["candles"]))


@bp.route("/api/trades")
def api_trades():
    return jsonify(list(shared_state.get_state()["trades"])[-20:])


@bp.route("/api/stream")
def api_stream():
    def event_stream():
        try:
            last_step = -1
            while True:
                s = shared_state.get_state()
                if s["step"] != last_step:
                    last_step = s["step"]
                    payload = {k: s[k] for k in [
                        "step", "price", "equity", "pnl_pct", "dopamine", "rpe",
                        "action", "confidence", "balance", "position"
                    ]}
                    payload["events"] = list(s["events"])[-3:]
                    yield f"data: {json.dumps(payload)}\n\n"
                time.sleep(0.1)
        except GeneratorExit:
            return
    return Response(event_stream(), mimetype="text/event-stream")
