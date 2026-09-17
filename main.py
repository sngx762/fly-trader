"""
Основной скрипт симуляции и обучения биомиметических трейдинг-агентов (FlyA и FlyB).
"""

import os
import time
import threading
import logging
import numpy as np
from dotenv import load_dotenv
import config
import shared_state
from market_data import load_ohlcv, generate_synthetic_data, normalize_features, FeatureEncoder
from fly_brain import MushroomBody, DopamineSystem
from trading_agent import TradingAgent
from paper_trader import PaperTrader
from tradingview_server import start_server

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def run_fly(csv_path: str, mode: str = "A", n_steps: int = 2000, seed: int = 42) -> dict:
    """Запуск симуляции торгового агента (мухи) на рыночных данных."""
    rng = np.random.default_rng(seed)
    
    try:
        df = load_ohlcv(csv_path)
    except FileNotFoundError:
        df = generate_synthetic_data(n=3000)

    norm_features = normalize_features(df, window=config.FEATURE_WINDOW)

    brain = MushroomBody(rng=rng)
    dopamine = DopamineSystem(mode=mode)
    agent = TradingAgent(rng=rng)
    trader = PaperTrader(balance=config.INITIAL_BALANCE)
    encoder = FeatureEncoder(n_sensory=config.N_SENSORY, rng=rng)

    steps_to_run = min(n_steps, len(norm_features))
    shared_state.update(mode=mode, running=True, total_steps=steps_to_run, fly_mode=mode)

    sleep_sec = float(os.getenv("SLEEP_SEC", "0.02"))

    for step_idx in range(steps_to_run):
        feat_vector = norm_features[step_idx]
        sensory_spikes = encoder.encode(feat_vector)

        mbon_spikes = brain.step(sensory_spikes)
        mbon_activity = brain.get_mbon_activity()

        action, confidence = agent.decide(mbon_activity)

        if step_idx == 0:
            logging.debug(f"Debug step 1: sensory_sum={sensory_spikes.sum():.4f}, mbon_activity={mbon_activity}, decision={action}, confidence={confidence}")

        current_price = float(df["close"].iloc[config.FEATURE_WINDOW + step_idx])
        trader.update_price(current_price)
        pnl_delta = trader.execute(action, current_price)

        da_info = dopamine.step(pnl_delta)

        if da_info["da_level"] > config.DA_BASELINE or da_info["is_punishment"]:
            brain.apply_dopamine(da_info["da_level"], is_punishment=da_info["is_punishment"])

        agent.update_readout(mbon_activity, action, pnl_delta, da_level=da_info["da_level"])

        # Обновление shared_state для 3D дашборда
        shared_state.update(
            step=step_idx + 1,
            price=current_price,
            balance=trader.cash,
            position=trader.position,
            equity=trader.get_equity(),
            pnl_pct=((trader.get_equity() - config.INITIAL_BALANCE) / config.INITIAL_BALANCE) * 100,
            dopamine=float(da_info["da_level"]),
            rpe=float(da_info["rpe"]),
            action=["HOLD", "BUY", "SELL"][action],
            confidence=float(confidence),
            fly_mode=mode,
        )

        df_idx = config.FEATURE_WINDOW + step_idx
        shared_state.push_candle({
            "t": step_idx,
            "o": float(df["open"].iloc[df_idx]),
            "h": float(df["high"].iloc[df_idx]),
            "l": float(df["low"].iloc[df_idx]),
            "c": current_price,
            "v": float(df["volume"].iloc[df_idx]),
        })

        if action in (1, 2):
            shared_state.push_trade({
                "time": step_idx,
                "action": ["HOLD", "BUY", "SELL"][action],
                "price": float(current_price),
                "pnl": float(pnl_delta),
            })

        if da_info["rpe"] > 0.5:
            shared_state.push_event("dopamine_burst", {"intensity": float(da_info["rpe"])})
        elif da_info["rpe"] < -0.5 and mode == "B":
            shared_state.push_event("punishment", {"intensity": float(abs(da_info["rpe"]))})

        if (step_idx + 1) % 200 == 0:
            eq = trader.get_equity()
            logging.info(f"[Fly {mode}] step {step_idx+1}, sleep={sleep_sec} | Price: {current_price:.2f} | Equity: {eq:.2f} | DA: {da_info['da_level']:.2f}")

        time.sleep(sleep_sec)

    shared_state.update(running=False, mode="finished")

    trades = trader.trades
    sell_trades = [t for t in trades if t["type"] == "SELL"]
    wins = len([t for t in sell_trades if t["pnl"] > 0])
    losses = len([t for t in sell_trades if t["pnl"] <= 0])
    total_trades = len(sell_trades)
    winrate = (wins / total_trades) if total_trades > 0 else 0.0
    final_equity = trader.get_equity()
    return_pct = ((final_equity - config.INITIAL_BALANCE) / config.INITIAL_BALANCE) * 100.0

    if total_trades == 0:
        logging.warning("⚠️ Муха не совершила ни одной сделки, проверь мозг")

    logging.info(f"--- Итоги Fly {mode} ---")
    logging.info(f"Финал. капитал: {final_equity:.2f} ({return_pct:+.2f}%)")
    logging.info(f"Всего сделок: {total_trades} (Побед: {wins}, Поражений: {losses})")
    logging.info(f"Win Rate: {winrate * 100:.1f}%\n")

    return {
        "mode": mode,
        "final_equity": final_equity,
        "return_pct": return_pct,
        "total_trades": total_trades,
        "wins": wins,
        "losses": losses,
        "winrate": winrate
    }


def main():
    """Запуск фонового сервера TradingView и симуляции двух мух (FlyA и FlyB)."""
    logging.info(f"⏱️ SLEEP_SEC={os.getenv('SLEEP_SEC', '0.02')}, LOOP={os.getenv('LOOP_SIMULATION', 'false')}")

    def _run_server():
        try:
            start_server(host="0.0.0.0", port=5001)
        except Exception as e:
            logging.warning(f"⚠️ TradingView webhook server не запустился: {e}")
            logging.warning("   Симуляция мух продолжится без вебхуков.")

    server_thread = threading.Thread(target=_run_server, daemon=True)
    server_thread.start()
    logging.info("🚀 TradingView webhook server & 3D Dashboard starting on http://0.0.0.0:5001 ...")

    csv_path = "data/BTCUSDT_1h.csv"
    
    loop_mode = os.getenv("LOOP_SIMULATION", "false").lower() == "true"

    while True:
        logging.info("=== Запуск FlyA (Чистое подкрепление) ===")
        res_a = run_fly(csv_path, mode="A", n_steps=2000, seed=42)

        logging.info("=== Запуск FlyB (С пептидом наказания) ===")
        res_b = run_fly(csv_path, mode="B", n_steps=2000, seed=42)

        logging.info("==========================================")
        logging.info("СРАВНЕНИЕ РЕЗУЛЬТАТОВ (FlyA vs FlyB):")
        logging.info(f"FlyA (Без наказания): Доходность = {res_a['return_pct']:+.2f}%, WinRate = {res_a['winrate']*100:.1f}%, Сделок = {res_a['total_trades']}")
        logging.info(f"FlyB (С наказанием):  Доходность = {res_b['return_pct']:+.2f}%, WinRate = {res_b['winrate']*100:.1f}%, Сделок = {res_b['total_trades']}")
        logging.info("==========================================")

        if loop_mode:
            logging.info("🔁 Новый цикл симуляции через 3 сек...")
            time.sleep(3)
        else:
            logging.info("✅ Симуляция завершена. Dashboard остаётся на http://localhost:5001/")
            logging.info("Нажмите Ctrl+C для выхода.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logging.info("Остановлено")
            break


if __name__ == "__main__":
    main()
