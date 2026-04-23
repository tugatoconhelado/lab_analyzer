from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import numpy as np

@dataclass
class InspectInfo:
    path: str
    name: str
    is_dataset: bool
    
    # We use field(default_factory=dict) so each instance gets its own empty dict
    attributes: Dict[str, Any] = field(default_factory=dict)

    # Optional fields for when it's a Dataset (Groups won't have these)
    shape: Optional[tuple] = None
    dtype: Optional[str] = None
    byte_order: Optional[str] = None    # e.g. "little-endian"
    size_bytes: Optional[int] = None    # e.g. 8 (for float64)
    filters: List[str] = field(default_factory=list) # e.g. ['gzip']

@dataclass
class Dataset:
    name: str = ""
    path: str = ""
    data: np.ndarray = field(default_factory=lambda: np.array([]))
    unit: str = ""
    metadata: dict = field(default_factory=dict)
    
    @property
    def ndim(self): return self.data.ndim
    
    @property
    def shape(self): return self.data.shape

    @property
    def timestamp(self): return self.metadata.get('timestamp', 0.0)

@dataclass
class Group:
    path: str = ""
    name: str = ""
    children: Dict[str, Any] = field(default_factory=dict)
    shape: Optional[tuple] = None

@dataclass
class Trace:
    """A virtual object that links an X dataset and a Y dataset."""
    name: str
    x_ds: Dataset  # Reference to the actual Dataset object
    y_ds: Dataset  # Reference to the actual Dataset object
    
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

@dataclass
class FitTraces:
    x_data: Dataset
    y_data: Dataset
    fit_x: np.ndarray = field(default_factory=lambda: np.array([]))
    fit_y: np.ndarray = field(default_factory=lambda: np.array([]))
    residuals: np.ndarray = field(default_factory=lambda: np.array([]))

@dataclass
class LineConfig:
    label: str = "Line"
    color: str = "#1f77b4"
    line_style: str = "-"
    line_width: float = 1.5
    marker: str = "o"
    marker_size: float = 6.0
    alpha: float = 1.0

@dataclass
class AxesConfig:
    # --- Content ---
    title: str = ""
    x_label: str = ""
    y_label: str = ""
    show_legend: bool = True
    legend_loc: str = "best"
    show_grid: bool = True
    
    # --- Scaling ---
    x_scale: str = "linear" # 'linear' or 'log'
    y_scale: str = "linear"
    x_limits: Optional[Tuple[float, float]] = None
    y_limits: Optional[Tuple[float, float]] = None
    
    # --- Export ---
    tight_layout: bool = True 
    use_sci_notation: bool = True

@dataclass
class WorkbenchAsset:

    name : str
    content : Any
    asset_type : str
    timestamp : datetime = field(default_factory=datetime.now)


class FitResult:
    
    def __init__(self, name, model, lmfit_result, source_trace):
        self.name = name
        self.result = lmfit_result

        self.timestamp = datetime.now()
        self.name = name
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
