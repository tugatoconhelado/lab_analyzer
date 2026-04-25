import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.core.structures import Dataset, LineConfig
from src.core.plot_object import PlotObject
from src.gui.plotting.plot_widget import PlotWindow
from PyQt5.QtCore import Qt


class PlotManager:

    def __init__(self, registry):
        self.registry = registry
        self._plots = {} # Store plot_id: (PlotObject, PlotWindow) pairs

    def create_new_window(self, trace_ids: list[int] | None = None):
        """
        Creates a new plot window for the given trace IDs.

         - Generates a unique plot name and PlotObject.
         - Registers the PlotObject in the registry.
         - Creates and shows a new PlotWindow linked to the PlotObject.
         - Tracks the window instance for lifecycle management.
        
        Parameters
        ----------
        trace_ids : list of int
            List of trace IDs to include in the new plot.

        Returns
        -------
        PlotWindow
            The created plot window instance.
        """

        plot_name = f"plot_{len(self._plots):02d}"
        plot_obj = PlotObject(plot_name=plot_name, registry=self.registry)
        self.registry.add(plot_name, plot_obj, source="PlotManager")
        plot_id = plot_obj.asset_id

        window = PlotWindow(plot_obj=plot_obj, plot_name=plot_name)
        
        self._plots[plot_id] = (plot_obj, window)
        window.setAttribute(Qt.WA_DeleteOnClose) # type: ignore[attr-defined]
        window.destroyed.connect(lambda: self._plots.pop(plot_id, None))
        
        window.show()
        

        if trace_ids:
            for tid in trace_ids:
                plot_obj.add_trace(tid)

        window.refresh()

    
    def add_trace_to_plot(self, plot_id: int, trace_id: int):
        """
        Adds a trace to an existing plot.

        Parameters
        ----------
        plot_id : int
            The ID of the plot to update.
        trace_id : int
            The ID of the trace to add.
        """
        plot = self._plots.get(plot_id, None)
        if plot:
            plot_obj, window = plot
            plot_obj.add_trace(trace_id)
            window.refresh()
    
    def clear_plot(self, plot_id: int):
        """
        Clears the plot with the given ID.
        
        Parameters
        ----------
        plot_id : int
            The ID of the plot to clear.
        """
        plot = self._plots.get(plot_id, None)
        if plot:
            plot_obj, window = plot
            plot_obj.clear_plot()
            window.refresh()


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    manager = PlotManager(None)
    manager.create_new_window(trace_ids=[1, 2])
    sys.exit(app.exec())