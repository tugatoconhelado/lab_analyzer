from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
from src.core.constants import AssetType

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
class Group:
    path: str = ""
    name: str = ""
    children: Dict[str, Any] = field(default_factory=dict)
    shape: Optional[tuple] = None

@dataclass
class WorkbenchAsset:

    name : str = ""
    kind : AssetType = AssetType.NONE
    timestamp : datetime = field(default_factory=datetime.now)
    asset_id : int = 0
