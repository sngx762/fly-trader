"""
Ядро нейросети грибовидного тела Drosophila: упрощенные LIF-нейроны (rate-coding), Kenyon cells, MBON и дофаминовая система RPE.
"""

import numpy as np
import config


class LIFNeuron:
    """Упрощенный LIF-нейрон (rate-coding / интегратор спайкового следа)."""

    def __init__(self):
        self.v = config.V_RESET
        self.refractory_counter = 0
        self.spike_trace = 0.0

    def step(self, input_current: float) -> bool:
        """Шаг симуляции нейрона."""
        self.spike_trace = self.spike_trace * config.SPIKE_DECAY + max(0.0, input_current)
        is_active = self.spike_trace > config.V_THRESH
        if is_active:
            self.v = config.V_THRESH
        else:
            self.v = config.V_RESET
        return is_active


class MushroomBody:
    """Грибовидное тело (Kenyon cells и MBON)."""

    def __init__(self, n_kenyon: int = config.N_KENYON, lr_reward: float = config.LR_REWARD, lr_punish: float = config.LR_PUNISH, rng: np.random.Generator = None):
        self.rng = rng if rng is not None else np.random.default_rng(42)
        self.n_kenyon = n_kenyon
        self.lr_reward = lr_reward
        self.lr_punish = lr_punish
        self.kc_neurons = [LIFNeuron() for _ in range(self.n_kenyon)]
        self.mbon_neurons = [LIFNeuron() for _ in range(config.N_MBON)]

        self.w_sens_kc = self.rng.uniform(-1.0, 1.0, (config.N_SENSORY, self.n_kenyon))
        self.w_kc_mbon = self.rng.uniform(0.1, 0.3, (self.n_kenyon, config.N_MBON))

        self.kc_spikes_prev = np.zeros(self.n_kenyon, dtype=float)
        self.mbon_spikes_prev = np.zeros(config.N_MBON, dtype=float)

    def step(self, sensory_spikes: np.ndarray) -> np.ndarray:
        """Шаг симуляции грибовидного тела: сенсоры -> KC -> MBON с топ-k разреженностью KC."""
        kc_currents = sensory_spikes @ self.w_sens_kc
        
        kc_spikes = np.array([1.0 if n.step(kc_currents[i]) else 0.0 for i, n in enumerate(self.kc_neurons)])
        if kc_spikes.sum() > 20:
            idx = np.argsort(kc_spikes)[-20:]
            mask = np.zeros_like(kc_spikes)
            mask[idx] = 1.0
            kc_spikes *= mask
        
        self.kc_spikes_prev = kc_spikes

        mbon_currents = kc_spikes @ self.w_kc_mbon

        mbon_spikes = np.zeros(config.N_MBON, dtype=float)
        for j, neuron in enumerate(self.mbon_neurons):
            if neuron.step(mbon_currents[j]):
                mbon_spikes[j] = 1.0

        self.mbon_spikes_prev = mbon_spikes
        return mbon_spikes

    def apply_dopamine(self, da_level: float, is_punishment: bool = False):
        """Хеббовское правило обновления синапсов KC->MBON под действием дофамина."""
        da_delta = da_level - config.DA_BASELINE
        if abs(da_delta) < 1e-5:
            return

        if is_punishment or da_delta < 0:
            lr = -self.lr_punish * abs(da_delta)
        else:
            lr = self.lr_reward * da_delta

        kc_traces = np.array([n.spike_trace for n in self.kc_neurons])
        mbon_traces = np.array([n.spike_trace for n in self.mbon_neurons])

        delta_w = lr * np.outer(kc_traces, mbon_traces)
        self.w_kc_mbon += delta_w
        np.clip(self.w_kc_mbon, config.W_MIN, config.W_MAX, out=self.w_kc_mbon)

    def get_mbon_activity(self) -> np.ndarray:
        """Возвращает спайковые следы MBON."""
        return np.array([n.spike_trace for n in self.mbon_neurons])


class DopamineSystem:
    """Дофаминовая система RPE (Reward Prediction Error)."""

    def __init__(self, mode: str = "A"):
        self.mode = mode
        self.da_level = config.DA_BASELINE
        self.expected_reward = 0.0
        self.reward_history = []

    def compute_rpe(self, actual_reward: float) -> float:
        """Вычисление ошибки предсказания награды (RPE)."""
        rpe = actual_reward - self.expected_reward
        self.expected_reward += config.RPE_ALPHA * rpe
        return rpe

    def step(self, pnl_delta: float) -> dict:
        """Шаг дофаминовой системы по изменению P&L."""
        normalized_reward = float(np.tanh(pnl_delta * 10.0))
        self.reward_history.append(normalized_reward)

        rpe = self.compute_rpe(normalized_reward)

        phasic = 0.0
        is_punishment = False

        if rpe > 0:
            phasic = rpe * config.DA_BURST_GAIN
        elif rpe < 0:
            if self.mode == "B":
                phasic = -config.DA_PUNISH_GAIN * abs(rpe)
                is_punishment = True
            else:
                phasic = 0.0
                is_punishment = False

        self.da_level = np.clip(config.DA_BASELINE + phasic, 0.0, 3.0)

        return {
            "da_level": self.da_level,
            "rpe": rpe,
            "is_punishment": is_punishment,
            "phasic": phasic
        }
