import os
import sys
from src.core.structures import LineConfig, AxesConfig
from typing import Dict, List

import logging
logger = logging.getLogger(__name__)


class PlotObject:
    """
    The 'Data Model' for a plot. Stores references, not the data itself.
    """
    def __init__(self, plot_id, registry):
        self.plot_id = plot_id
        self.registry = registry
        self.trace_ids = []  # List of IDs to look up in Registry
        
        # Composition: The PlotObject 'has an' AxesConfig
        self.axes_config = AxesConfig(title=plot_id)
        
        # Map: trace_id -> LineConfig (Each trace gets its own style)
        self.trace_configs: Dict[str, LineConfig] = {}
        self.trace_ids: List[str] = []

    def add_trace(self, trace_id):
        if trace_id not in self.trace_ids:
            self.trace_ids.append(trace_id)
            # Create a default config for this specific trace
            self.trace_configs[trace_id] = LineConfig(label=trace_id)

    def remove_trace(self, trace_id):
        if trace_id in self.trace_ids:
            self.trace_ids.remove(trace_id)
            self.trace_configs.pop(trace_id, None)