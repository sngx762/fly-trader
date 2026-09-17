"""
Загрузка рыночных данных OHLCV, расчет признаков с оконным z-score, сессионными фичами и кодирование в спайки.
"""

import numpy as np
import pandas as pd
import config


def load_ohlcv(path: str) -> pd.DataFrame:
    """Загрузка OHLCV данных из CSV файла без fallback на синтетику."""
    try:
        df = pd.read_csv(path)
        required_cols = ["timestamp", "open", "high", "low", "close", "volume"]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Отсутствует обязательная колонка '{col}' в файле {path}")
        return df
    except FileNotFoundError:
        raise FileNotFoundError(f"Файл рыночных данных не найден по пути: {path}")
    except Exception as e:
        if isinstance(e, (FileNotFoundError, ValueError)):
            raise e
        raise ValueError(f"Ошибка чтения CSV файла {path}: {e}")


def generate_synthetic_data(n: int = 1000) -> pd.DataFrame:
    """Генерация синтетических OHLCV данных при отсутствии CSV файла."""
    np.random.seed(42)
    prices = 100.0 + np.cumsum(np.random.normal(0, 0.5, n))
    highs = prices + np.abs(np.random.normal(0.2, 0.1, n))
    lows = prices - np.abs(np.random.normal(0.2, 0.1, n))
    opens = prices + np.random.normal(0, 0.1, n)
    volumes = np.random.uniform(1000, 10000, n)
    df = pd.DataFrame({
        "timestamp": pd.date_range(start="2026-01-01", periods=n, freq="h"),
        "open": opens,
        "high": highs,
        "low": lows,
        "close": prices,
        "volume": volumes
    })
    return df


def normalize_features(df: pd.DataFrame, window: int = 20) -> np.ndarray:
    """Расчет логарифмических доходностей с z-score по окну, объема и сессионных фичей."""
    close = df["close"].values
    volume = df["volume"].values

    log_returns = np.zeros_like(close)
    log_returns[1:] = np.log(close[1:] / close[:-1])

    vol_mean = np.mean(volume)
    vol_std = np.std(volume) if np.std(volume) > 0 else 1.0
    norm_vol = (volume - vol_mean) / vol_std

    # Session features (UTC hours)
    timestamps = pd.to_datetime(df["timestamp"])
    hour_utc = timestamps.dt.hour.values
    is_london = ((hour_utc >= 8) & (hour_utc < 16)).astype(float)
    is_ny = ((hour_utc >= 13) & (hour_utc < 21)).astype(float)
    is_overlap = ((hour_utc >= 13) & (hour_utc < 16)).astype(float)

    n = len(close)
    features_list = []

    for i in range(window, n):
        win_returns = log_returns[i - window + 1:i + 1]
        mu = win_returns.mean()
        sigma = win_returns.std() + 1e-9
        win_returns_norm = (win_returns - mu) / sigma
        win_returns_norm = np.clip(win_returns_norm, -3, 3) / 3  # в [-1, 1]

        win_vol = norm_vol[i - window + 1:i + 1]
        sess_feat = np.array([is_london[i], is_ny[i], is_overlap[i]])

        feat = np.concatenate([win_returns_norm, win_vol, sess_feat])
        features_list.append(feat)

    if not features_list:
        feat = np.zeros(window * 2 + 3)
        features_list.append(feat)

    return np.array(features_list)


class FeatureEncoder:
    """Класс-обертка для кодирования признаков в сенсорные активности (rate coding) без случайности."""

    def __init__(self, n_features: int, n_sensory: int = config.N_SENSORY, rng: np.random.Generator = None):
        self.rng = rng if rng is not None else np.random.default_rng(42)
        self.proj_matrix = self.rng.uniform(-1.0, 1.0, (n_features, n_sensory))

    def encode(self, features: np.ndarray) -> np.ndarray:
        """Преобразование вектора признаков в непрерывную активность (rate-coding)."""
        projected = features @ self.proj_matrix
        probs = 1.0 / (1.0 + np.exp(-projected))
        return probs
