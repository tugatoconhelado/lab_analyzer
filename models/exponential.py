import numpy as np
from models.labmodel import LabModel

class Exponential(LabModel):

    model_name = "SingleExponential"

    def fit_func(self, x, T1=55.5, amplitude=0.2, background=1.0):
        """
        Standard exponential decay.
        x is usually time in microseconds (us).
        """
        # Using np.exp for vectorization and stability
        return background + amplitude * np.exp(-x / T1)

    def guess_initial_params(self, x, y):
        """
        Automated guessing to ensure the fit converges quickly.
        """
        # 1. Background is usually the value at the end of the decay (long times)
        bg_guess = np.median(y[-10:]) 
        
        # 2. Amplitude is the difference between the start and the background
        amp_guess = y[0] - bg_guess
        
        # 3. T1 guess: find where the signal has dropped roughly by 1/e
        # Defaulting to 1/4 of the x-range is a safe fallback
        t1_guess = np.max(x) / 4.0
        
        self.params['background'].set(value=bg_guess, min=0)
        self.params['amplitude'].set(value=amp_guess)
        self.params['T1'].set(value=t1_guess, min=0) # T1 must be positive

        return self.params