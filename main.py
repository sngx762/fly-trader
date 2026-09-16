"""
Основной скрипт симуляции и обучения биомиметических трейдинг-агентов (FlyA и FlyB).
"""

import os
import threading
import numpy as np
import config
from market_data import load_ohlcv, generate_synthetic_data, normalize_features, FeatureEncoder
from fly_brain import MushroomBody, DopamineSystem
from trading_agent import TradingAgent
from paper_trader import PaperTrader
from tradingview_server import start_server


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

    for step_idx in range(steps_to_run):
        feat_vector = norm_features[step_idx]
        sensory_spikes = encoder.encode(feat_vector)

        mbon_spikes = brain.step(sensory_spikes)
        mbon_activity = brain.get_mbon_activity()

        action, confidence = agent.decide(mbon_activity)

        if step_idx == 0:
            print(f"Debug step 1: sensory_sum={sensory_spikes.sum():.4f}, mbon_activity={mbon_activity}, decision={action}, confidence={confidence}")

        current_price = float(df["close"].iloc[config.FEATURE_WINDOW + step_idx])
        trader.update_price(current_price)
        pnl_delta = trader.execute(action, current_price)

        da_info = dopamine.step(pnl_delta)

        if da_info["da_level"] > config.DA_BASELINE or da_info["is_punishment"]:
            brain.apply_dopamine(da_info["da_level"], is_punishment=da_info["is_punishment"])

        agent.update_readout(mbon_activity, action, pnl_delta, da_level=da_info["da_level"])

        if (step_idx + 1) % 200 == 0:
            eq = trader.get_equity()
            print(f"[Fly {mode}] Step {step_idx + 1}/{steps_to_run} | Price: {current_price:.2f} | "
                  f"Equity: {eq:.2f} | DA: {da_info['da_level']:.2f} | RPE: {da_info['rpe']:.4f}")

    trades = trader.trades
    sell_trades = [t for t in trades if t["type"] == "SELL"]
    wins = len([t for t in sell_trades if t["pnl"] > 0])
    losses = len([t for t in sell_trades if t["pnl"] <= 0])
    total_trades = len(sell_trades)
    winrate = (wins / total_trades) if total_trades > 0 else 0.0
    final_equity = trader.get_equity()
    return_pct = ((final_equity - config.INITIAL_BALANCE) / config.INITIAL_BALANCE) * 100.0

    if total_trades == 0:
        print("⚠️ Муха не совершила ни одной сделки, проверь мозг")

    print(f"\n--- Итоги Fly {mode} ---")
    print(f"Финальный капитал: {final_equity:.2f} ({return_pct:+.2f}%)")
    print(f"Всего сделок: {total_trades} (Побед: {wins}, Поражений: {losses})")
    print(f"Win Rate: {winrate * 100:.1f}%\n")

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
    def _run_server():
        try:
            start_server(host="0.0.0.0", port=5001)
        except Exception as e:
            print(f"⚠️ TradingView webhook server не запустился: {e}")
            print("   Симуляция мух продолжится без вебхуков.")

    server_thread = threading.Thread(target=_run_server, daemon=True)
    server_thread.start()
    print("🚀 TradingView webhook server starting on port 5001...")

    csv_path = "data/BTCUSDT_1h.csv"
    print("=== Запуск FlyA (Чистое подкрепление) ===")
    res_a = run_fly(csv_path, mode="A", n_steps=2000, seed=42)

    print("=== Запуск FlyB (С пептидом наказания) ===")
    res_b = run_fly(csv_path, mode="B", n_steps=2000, seed=42)

    print("==========================================")
    print("СРАВНЕНИЕ РЕЗУЛЬТАТОВ (FlyA vs FlyB):")
    print(f"FlyA (Без наказания): Доходность = {res_a['return_pct']:+.2f}%, WinRate = {res_a['winrate']*100:.1f}%, Сделок = {res_a['total_trades']}")
    print(f"FlyB (С наказанием):  Доходность = {res_b['return_pct']:+.2f}%, WinRate = {res_b['winrate']*100:.1f}%, Сделок = {res_b['total_trades']}")
    print("==========================================")


if __name__ == "__main__":
    main()
