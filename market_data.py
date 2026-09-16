"""
Загрузка рыночных данных OHLCV, расчет признаков с expanding-нормализацией и кодирование в спайки.
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
    """Расчет логарифмических доходностей и объема с expanding-нормализацией (без заглядывания в будущее)."""
    close = df["close"].values
    volume = df["volume"].values

    log_returns = np.zeros_like(close)
    log_returns[1:] = np.log(close[1:] / close[:-1])

    vol_mean = np.mean(volume)
    vol_std = np.std(volume) if np.std(volume) > 0 else 1.0
    norm_vol = (volume - vol_mean) / vol_std

    n = len(close)
    features_list = []

    for i in range(window, n):
        win_returns = log_returns[i - window + 1:i + 1]
        win_vol = norm_vol[i - window + 1:i + 1]
        feat = np.concatenate([win_returns, win_vol])
        features_list.append(feat)

    if not features_list:
        feat = np.zeros(window * 2)
        features_list.append(feat)

    features_matrix = np.array(features_list)

    norm_features = np.zeros_like(features_matrix)
    for i in range(len(features_matrix)):
        f_min = features_matrix[:i+1].min(axis=0)
        f_max = features_matrix[:i+1].max(axis=0)
        norm_features[i] = (features_matrix[i] - f_min) / (f_max - f_min + 1e-9)

    return norm_features


class FeatureEncoder:
    """Класс-обертка для кодирования признаков в сенсорные активности (rate coding) без случайности."""

    def __init__(self, n_sensory: int = config.N_SENSORY, rng: np.random.Generator = None):
        self.rng = rng if rng is not None else np.random.default_rng(42)
        self.proj_matrix = self.rng.uniform(-1.0, 1.0, (config.FEATURE_WINDOW * 2, n_sensory))

    def encode(self, features: np.ndarray) -> np.ndarray:
        """Преобразование вектора признаков в непрерывную активность (rate-coding)."""
        projected = features @ self.proj_matrix
        probs = 1.0 / (1.0 + np.exp(-projected))
        return probs
