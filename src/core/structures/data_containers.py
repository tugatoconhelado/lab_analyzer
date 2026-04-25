from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import numpy as np

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from src.core.constants import AssetType
from src.core.structures import WorkbenchAsset


@dataclass
class Dataset(WorkbenchAsset):
    path: str = ""
    data: np.ndarray = field(default_factory=lambda: np.array([]))
    unit: str = ""
    metadata: dict = field(default_factory=dict)
    kind: AssetType = AssetType.DATASET
    
    @property
    def ndim(self): return self.data.ndim
    
    @property
    def shape(self): return self.data.shape


@dataclass
class Trace(WorkbenchAsset):
    """A virtual object that links an X dataset and a Y dataset."""
    x_ds: Dataset  = field(default_factory=lambda: Dataset())
    y_ds: Dataset  = field(default_factory=lambda: Dataset())
    kind: AssetType = AssetType.TRACE
    
    @property
    def data(self):
        # Returns a 2D view (X, Y) without copying the underlying arrays
        return np.vstack((self.x_ds.data, self.y_ds.data))
    
    @property
    def x(self):
        return self.x_ds.data

    @property
    def y(self):
        return self.y_ds.data
    
    @property
    def shape(self):
        return self.x_ds.shape, self.y_ds.shape

    def __repr__(self):
        return f"Trace({self.name}: {self.y_ds.name} vs {self.x_ds.name})"


class FitResult(WorkbenchAsset):
    
    def __init__(self, name, model, lmfit_result, source_trace):
        super().__init__(name=name, kind=AssetType.FIT)
        self.result = lmfit_result

        self.model = model
        self.result = lmfit_result
        
        # LINKING: We store the actual objects
        self.trace = source_trace
        
        # We also store their names in case we need to look them up in the registry later
        self.x_name = source_trace.x_ds.name
        self.y_name = source_trace.y_ds.name

        # The Generated Curve
        self.curve = Dataset(
            name=f"{name}_curve",
            data=lmfit_result.best_fit
        )
        self.residuals = Dataset(
            name=f"{name}_residuals",
            data=lmfit_result.residual
        )
        self.report = lmfit_result.fit_report()
        # Extract key metrics for quick access in the GUI
        self.chisqr = lmfit_result.chisqr
        self.redchi = lmfit_result.redchi
        self.params = model.get_parameter_list(lmfit_result.params)


    def __repr__(self):
        return f"<FitResult: {self.name} ({self.model}) | RedChi: {self.redchi:.4e}>"
    
    def eval_at(self, new_x):
        """Perform operations: Calculate Y for any arbitrary X."""
        return self.model.eval(self.result.params, x=new_x)


if __name__ == "__main__":
    # Quick test to ensure structures work as expected
    x_ds = Dataset(name="X Data", data=np.random.random(100))
    y_ds = Dataset(name="Y Data", data=np.random.random(100))
    trace = Trace(name="Test Trace", x_ds=x_ds, y_ds=y_ds)
    print(x_ds.kind, x_ds.shape)