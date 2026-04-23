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
    path: str = ""
    name: str = ""
    data: np.ndarray = field(default_factory=lambda: np.array([]))
    ndim: int = 0
    shape: Optional[tuple] = None
    timestamp: float = 0.0

@dataclass
class Group:
    path: str = ""
    name: str = ""
    children: Dict[str, Any] = field(default_factory=dict)
    shape: Optional[tuple] = None

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