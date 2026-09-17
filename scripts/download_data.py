"""
Скрипт для скачивания исторических данных OHLCV с Binance, Yahoo Finance или Twelve Data.
"""

import os
import argparse
import requests
import pandas as pd
import yfinance as yf
from dotenv import load_dotenv
from twelvedata import TDClient

load_dotenv()


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


def download_yahoo(symbol: str = "XAUUSD=X", period: str = "60d", interval: str = "1h") -> pd.DataFrame:
    """Скачивание спот данных с Yahoo Finance."""
    print(f"Запрос данных с Yahoo Finance: {symbol} ({interval}, {period})...")
    df = yf.download(symbol, interval=interval, period=period, progress=False)
    if df.empty:
        raise ValueError(f"Yahoo Finance не вернул данных для {symbol}")
    
    # Приведение multi-index колонок к плоским именам
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    df = df.reset_index()
    # Ищем колонку даты/времени
    date_col = "Datetime" if "Datetime" in df.columns else ("Date" if "Date" in df.columns else df.columns[0])
    
    df = df.rename(columns={
        date_col: "timestamp",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume"
    })
    
    # Заполняем volume нулями, если его нет
    if "volume" not in df.columns:
        df["volume"] = 0.0

    return df[["timestamp", "open", "high", "low", "close", "volume"]]


def download_twelvedata(symbol: str = "XAU/USD", interval: str = "1h", outputsize: int = 1000) -> pd.DataFrame:
    """Скачивание спот данных с Twelve Data API."""
    api_key = os.getenv("TWELVEDATA_API_KEY")
    if not api_key or api_key == "your_key_here":
        raise ValueError("TWELVEDATA_API_KEY не задан в .env")
    
    print(f"Запрос данных с Twelve Data: {symbol} ({interval}, outputsize={outputsize})...")
    td = TDClient(apikey=api_key)
    ts = td.time_series(symbol=symbol, interval=interval, outputsize=outputsize, timezone="UTC")
    df = ts.as_pandas().reset_index()
    df = df.rename(columns={"datetime": "timestamp"})
    df.columns = [str(c).lower() for c in df.columns]
    
    if "volume" not in df.columns:
        df["volume"] = 0.0
        
    return df[["timestamp", "open", "high", "low", "close", "volume"]]


def main():
    parser = argparse.ArgumentParser(description="Скачивание OHLCV с Binance, Yahoo или Twelve Data")
    parser.add_argument("--source", type=str, choices=["binance", "yahoo", "twelvedata"], default="binance", help="Источник данных")
    parser.add_argument("--symbol", type=str, default="", help="Торговый символ (например, BTCUSDT, XAUUSD=X, XAU/USD)")
    parser.add_argument("--interval", type=str, default="1h", help="Таймфрейм (например, 1h)")
    parser.add_argument("--limit", type=int, default=1000, help="Количество свечей / лимит")
    parser.add_argument("--output", type=str, default="", help="Путь для сохранения CSV")
    args = parser.parse_args()

    # Дефолтные значения в зависимости от источника
    if not args.symbol:
        args.symbol = "BTCUSDT" if args.source == "binance" else ("XAUUSD=X" if args.source == "yahoo" else "XAU/USD")
    if not args.output:
        args.output = "data/BTCUSDT_1h.csv" if args.source == "binance" else "data/XAUUSD_1h.csv"

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)

    try:
        if args.source == "binance":
            df = download_binance_klines(symbol=args.symbol, interval=args.interval, limit=args.limit)
        elif args.source == "yahoo":
            df = download_yahoo(symbol=args.symbol, interval=args.interval)
        elif args.source == "twelvedata":
            df = download_twelvedata(symbol=args.symbol, interval=args.interval, outputsize=args.limit)
        else:
            raise ValueError(f"Неизвестный источник: {args.source}")

        df.to_csv(args.output, index=False)
        print(f"Успешно сохранено {len(df)} строк в {args.output}")
    except Exception as e:
        print(f"Ошибка при скачивании данных: {e}")


if __name__ == "__main__":
    main()
