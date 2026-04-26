import os
import sys
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.core.structures import Dataset, LineConfig
from src.core.plot_object import PlotObject
from src.gui.plotting.plot_widget import PlotWindow
from PyQt5.QtWidgets import QFileDialog

logger = logging.getLogger(__name__)


class PlotManager:

    def __init__(self, registry, ui):
        self.registry = registry
        self.ui = ui
        self._plots = {} # Store plot_id: (PlotObject, PlotWindow) pairs
        self._plot_counter = 0

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
        plot_name = f"plot_{self._plot_counter:02d}"
        plot_obj = PlotObject(plot_name=plot_name, registry=self.registry)
        if trace_ids:
            for tid in trace_ids:
                plot_obj.add_trace(tid)
        self.registry.add(plot_name, plot_obj, source="PlotManager")
        plot_id = plot_obj.asset_id

        window = PlotWindow(parent=self.ui, plot_obj=plot_obj, plot_name=plot_name)
        
        self._plots[plot_id] = (plot_obj, window)

        self._plot_counter += 1
        
        window.show()
        window.refresh()
        return window

    def close_plot(self, plots):
        """
        Closes the plot window while keeping it available for reopening.

        Parameters
        ----------
        plots : list of int
            List of plot IDs to close.
        """
        for plot_id in plots:
            if plot_id in self._plots:
                del self._plots[plot_id]

    def reopen_plot(self, plots: list[int]):
        """
        Reopens a previously hidden plot window.

        Parameters
        ----------
        plots : list of int
            List of plot IDs to reopen.

        Returns
        -------
        PlotWindow | None
            The reopened window, or None if plot_id does not exist.
        """
        for plot_id in plots:
            plot = self._plots.get(plot_id, None)
            if plot:
                _, window = plot
                window.showNormal()
                window.show()
                window.refresh()
                return window
        return None

    def export_plot(self, plots: list[int], export_format: str):
        """
        Exports plots to an image file.

        Parameters
        ----------
        plot_id : list[int]
            List of plot IDs to export.
        export_format : str
            File format, one of: png, svg, pdf.
        """
        for plot_id in plots:
            plot = self._plots.get(plot_id, None)
            if plot is None:
                logger.warning("Cannot export plot %s: plot not found.", plot_id)
                return

            _, window = plot

            fmt = export_format.lower().strip(".")
            if fmt not in {"png", "svg", "pdf"}:
                logger.warning("Unsupported plot export format: %s", export_format)
                return

            default_name = f"{window.plot_name}.{fmt}"
            filter_text = f"{fmt.upper()} Files (*.{fmt});;All Files (*)"
            file_path, _ = QFileDialog.getSaveFileName(
                self.ui,
                "Export Plot",
                default_name,
                filter_text,
            )

            if not file_path:
                return

            if not file_path.lower().endswith(f".{fmt}"):
                file_path = f"{file_path}.{fmt}"

            window.plot_canvas.fig.savefig(file_path, format=fmt)
            logger.info("Exported plot %s to %s", plot_id, file_path)
            return
    
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
    manager = PlotManager(None, None)
    manager.create_new_window(trace_ids=[1, 2])
    sys.exit(app.exec())