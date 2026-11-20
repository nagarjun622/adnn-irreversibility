import os
import random
import numpy as np
import torch

PROJECT_DIR = "/content/drive/MyDrive/adnn_irreversibility"
DATA_DIR = PROJECT_DIR + "/data"
HIDDEN_DIR = PROJECT_DIR + "/hidden_states"
LOG_DIR = PROJECT_DIR + "/logs"
RESULT_DIR = PROJECT_DIR + "/results"

SEED = 42  # same seed everywhere, so results can be repeated

def make_folders():
    for folder in [DATA_DIR, HIDDEN_DIR, LOG_DIR, RESULT_DIR]:
        os.makedirs(folder, exist_ok=True)

def set_seed(seed=SEED):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
