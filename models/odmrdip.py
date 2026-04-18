# models/nv_models.py
import numpy as np
from models.labmodel import LabModel

class OdmrDip(LabModel):
    def fit_func(self, x, amplitude=-0.05, center=2.87, sigma=0.01, background=1.0):
        return background + (amplitude * sigma**2) / ((x - center)**2 + sigma**2)

