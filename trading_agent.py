"""
Торговый агент на основе MBON-активности с нормализацией активности и вероятностным выбором по softmax: принятие решений и обновление readout-весов.
"""

import numpy as np
import config


class TradingAgent:
    """Торговый агент с линейным считывателем (readout) из активности MBON."""

    def __init__(self, decision_threshold: float = config.DECISION_THRESHOLD, rng: np.random.Generator = None):
        self.rng = rng if rng is not None else np.random.default_rng(42)
        self.decision_threshold = decision_threshold
        self.readout = self.rng.normal(0, 0.1, (config.N_MBON, 3))

    def decide(self, mbon_activity: np.ndarray) -> tuple:
        """Принятие торгового решения на основе softmax-вероятностей активности MBON."""
        m = mbon_activity / (np.linalg.norm(mbon_activity) + 1e-9)
        logits = m @ self.readout
        exp_logits = np.exp(logits - np.max(logits))
        probs = exp_logits / np.sum(exp_logits)

        action = int(self.rng.choice(3, p=probs))
        confidence = float(probs[action])

        if confidence < self.decision_threshold:
            action = 0  # hold по умолчанию при низкой уверенности

        return action, confidence

    def update_readout(self, mbon_activity: np.ndarray, action: int, reward: float, da_level: float = 0.2, lr: float = 0.001):
        """Градиентное обновление readout-весов с модулированием дофамином (DA level)."""
        m = mbon_activity / (np.linalg.norm(mbon_activity) + 1e-9)
        logits = m @ self.readout
        exp_logits = np.exp(logits - np.max(logits))
        probs = exp_logits / np.sum(exp_logits)

        target = np.zeros(3)
        target[action] = 1.0

        effective_lr = lr * (da_level / config.DA_BASELINE)
        error = np.tanh(reward) * (target - probs)
        self.readout += effective_lr * np.outer(m, error)
