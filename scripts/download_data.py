"""
Скрипт для скачивания исторических данных OHLCV с публичного API Binance REST v3.
"""

import os
import argparse
import requests
import pandas as pd


def download_binance_klines(symbol: str = "BTCUSDT", interval: str = "1h", limit: int = 1000) -> pd.DataFrame:
    """Скачивание свечей с Binance API и преобразование в DataFrame."""
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol.upper(),
        "interval": interval,
        "limit": limit
    }

    print(f"Запрос данных с Binance: {symbol} ({interval}), лимит: {limit} свечей...")
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    rows = []
    for k in data:
        timestamp = pd.to_datetime(k[0], unit='ms')
        open_p = float(k[1])
        high_p = float(k[2])
        low_p = float(k[3])
        close_p = float(k[4])
        volume = float(k[5])
        rows.append({
            "timestamp": timestamp,
            "open": open_p,
            "high": high_p,
            "low": low_p,
            "close": close_p,
            "volume": volume
        })

    df = pd.DataFrame(rows)
    return df


def main():
    parser = argparse.ArgumentParser(description="Скачивание OHLCV с Binance API")
    parser.add_argument("--symbol", type=str, default="BTCUSDT", help="Торговая пара (например, BTCUSDT)")
    parser.add_argument("--interval", type=str, default="1h", help="Таймфрейм (например, 1h, 15m, 1d)")
    parser.add_argument("--limit", type=int, default=1000, help="Количество свечей (макс 1000)")
    parser.add_argument("--output", type=str, default="data/BTCUSDT_1h.csv", help="Путь для сохранения CSV")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)

    try:
        df = download_binance_klines(symbol=args.symbol, interval=args.interval, limit=args.limit)
        df.to_csv(args.output, index=False)
        print(f"Успешно сохранено {len(df)} строк в {args.output}")
    except Exception as e:
        print(f"Ошибка при скачивании данных: {e}")


if __name__ == "__main__":
    main()
