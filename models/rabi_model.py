# models/nv_models.py
import numpy as np
from models.labmodel import LabModel


class RabiOscillation(LabModel):

    name = "Rabi"

    def fit_func(self, x, amp=1, freq=1, phase=0, offset=0):
        return amp * np.sin(2 * np.pi * freq * x + phase) + offset