from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
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
class DataResult:
    path: str
    name: str
    data: np.ndarray 
    ndim: int 
    timestamp: float

@dataclass
class FitTraces:
    x_data: DataResult
    y_data: DataResult
    fit_x: np.ndarray
    fit_y: np.ndarray
    residuals: np.ndarray