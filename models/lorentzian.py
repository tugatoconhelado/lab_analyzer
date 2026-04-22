import numpy as np
from models.labmodel import LabModel

class OdmrLorentzian(LabModel):

    model_name = "ODMRLorentzian"
    
    def fit_func(self, x, amplitude=-0.05, center=2.87, sigma=0.01, background=1.0):
        """A simple Lorentzian dip for NV ODMR."""
        return background + (amplitude * sigma**2) / ((x - center)**2 + sigma**2)

    def guess_initial_params(self, x, y):
        """Automatically guess parameters based on the data provided."""
        self.params['background'].set(value=np.max(y))
        self.params['center'].set(value=x[np.argmin(y)]) # Guess center at the minimum
        self.params['amplitude'].set(value=np.min(y) - np.max(y))
        self.params['sigma'].set(value=0.005, min=0) # Constrain sigma to be positive
        return self.params