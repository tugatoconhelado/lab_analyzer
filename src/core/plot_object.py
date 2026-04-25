import os
import sys
from src.core.structures import LineConfig, AxesConfig, WorkbenchAsset
from src.core.constants import AssetType
from typing import Dict, List

import logging
logger = logging.getLogger(__name__)


class PlotObject(WorkbenchAsset):
    """
    The 'Data Model' for a plot. Stores references, not the data itself.
    """
    def __init__(self, plot_name, registry):
        super().__init__(name=plot_name)
        self.registry = registry
        self.kind = AssetType.PLOT
        # Composition: The PlotObject 'has an' AxesConfig
        self.axes_config = AxesConfig(title=plot_name)
        
        # Map: trace_id -> LineConfig (Each trace gets its own style)
        self.trace_configs: Dict[int, LineConfig] = {}
        self.trace_ids: List[int] = []

    def add_trace(self, trace_id):
        if trace_id not in self.trace_ids:
            if not self.verify_trace_id(trace_id):
                return
            self.trace_ids.append(trace_id)
            # Create a default config for this specific trace
            self.trace_configs[trace_id] = LineConfig(label=trace_id)

    def remove_trace(self, trace_id):
        if trace_id in self.trace_ids:
            self.trace_ids.remove(trace_id)
            self.trace_configs.pop(trace_id, None)

    def verify_trace_id(self, trace_id):
        """
        Verifies that the given trace_id corresponds to 
        a valid Trace in the registry.

        Parameters
        ----------
        trace_id : int
            The ID of the trace to verify.
            
        Returns
        -------
        bool
            True if the trace_id is valid and corresponds
            to a Trace or Dataset asset, False otherwise.
        """
        obj = self.registry.get(trace_id)
        if obj is None:
            return False
        if obj.kind & AssetType.TRACE:
            return True
        elif obj.kind & AssetType.DATASET:
            logger.warning(f"Asset ID '{trace_id}' is a Dataset, expected a Trace for PlotObject '{self.name}'.")
            logger.warning(f"Dataset '{obj.name}' can still be added as a trace, but will be plotted with default styling.")
            return True
        
        return False

    def clear_plot(self):
        self.trace_ids.clear()
        self.trace_configs.clear()

    def get_data(self, trace_id: int):
        """
        Retrieves the data associated with a given trace ID.
        
        Parameters
        ----------
        trace_id : int
            The ID of the trace to retrieve data for.

        Returns
        -------
        Dataset or Trace object
            The data object associated with the trace ID, or None if not found
            or if the asset type is incorrect.
        """
        if trace_id in self.trace_ids:
            obj = self.registry.get(trace_id)
            if obj.kind & AssetType.TRACE or obj.kind & AssetType.DATASET:
                return obj
        else:
            logger.warning(f"Trace ID '{trace_id}' not found in PlotObject '{self.name}'.")
            return None
        
    def get_trace_config(self, trace_id):

        if trace_id not in self.trace_configs:
            logger.warning(f"No specific LineConfig found for Trace ID '{trace_id}' in PlotObject '{self.name}'. Using default.")
            return LineConfig(label=trace_id)
        return self.trace_configs[trace_id]