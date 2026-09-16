"""
Конфигурация гиперпараметров модели биомиметического трейдинг-агента (Drosophila Mushroom Body).
"""

N_SENSORY = 64
N_KENYON = 256
N_MBON = 16
N_DOPAMINE_PAM = 8  # награда
N_DOPAMINE_PPL = 4  # наказание

DT = 0.01
TAU_MEMBRANE = 20.0
V_THRESH = 5.0
V_RESET = 0.0
REFRACTORY = 5
SPIKE_DECAY = 0.9

DA_BASELINE = 0.2
DA_BURST_GAIN = 1.5
DA_DECAY = 0.95
DA_PUNISH_GAIN = 1.2

RPE_GAMMA = 0.9
RPE_ALPHA = 0.1

LR_REWARD = 0.012
LR_PUNISH = 0.02
W_MIN = 0.0
W_MAX = 1.0

FEATURE_WINDOW = 20
DECISION_THRESHOLD = 0.15
MAX_POSITION = 1.0
INITIAL_BALANCE = 100.0
FLY_MODE = "A"  # "A" = без наказания, "B" = с наказанием
