from dataclasses import dataclass, field
from typing import Optional, Tuple


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