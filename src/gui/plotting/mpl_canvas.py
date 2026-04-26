from PyQt5.QtWidgets import QWidget

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import numpy as np

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from src.core.structures import LineConfig, AxesConfig
from src.core.plot_object import PlotObject


class MplCanvas(FigureCanvasQTAgg):


    def __init__(self, parent=None, width=5, height=4, dpi=100):

        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        self._lines = {}
        self._axes = {'ax_00': self.axes}
        self._fit_line_counter = 0
        self._data_line_counter = 0
        
        # Initialize the canvas
        super().__init__(self.fig)
        self.setParent(parent)

    def update_from_object(self, obj: PlotObject):
        """Updates the plot based on the provided PlotObject."""
        self.clear_plot()
        for trace_id in obj.trace_ids:
            trace = obj.get_data(trace_id)
            line_cfg = obj.get_trace_config(trace_id)
            if trace and line_cfg:
                data = trace.data
                if data is None:
                    continue
                if data.ndim == 2:
                    x_data, y_data = data
                elif data.ndim == 1:
                    x_data = np.arange(len(data))
                    y_data = data
                else:
                    continue
                self.add_data_line(x_data, y_data, line_id=trace_id)
                self.apply_line_config(trace_id, line_cfg)

        self.apply_axes_config(obj.name, obj.axes_config)

    def clear_plot(self):
        """Clears the current plot and resets line tracking."""
        self.axes.clear()
        self._lines.clear()
        self._fit_line_counter = 0
        self._data_line_counter = 0
        self.draw()

    def add_data_line(self, x_data: np.ndarray, y_data: np.ndarray, line_id: int | None = None) -> int | None:
        """
        Standard method to refresh the plot with new Dataset.
        """
        if line_id is None:
            return None
        line = self.axes.plot(x_data, y_data, 'o', color='blue', label="Data")[0]
        self.draw()
        self._lines[line_id] = line
        self._data_line_counter += 1

        return line_id 

    def add_fit_line(self, x_fit, y_fit):
        """Adds a fit line to the existing plot."""
        line = self.axes.plot(x_fit, y_fit, color='red', linewidth=1.5, label="Fit")[0]
        self.axes.legend()
        self.draw()
        if "fit" in self._lines:
            line_id = f"fit_{self._fit_line_counter:02d}"
        else:
            line_id = "fit"
        self._lines[line_id] = line
        self._fit_line_counter += 1
        return line_id

    def apply_line_config(self, line_id: int | None, config: LineConfig):
        """Updates the plot's appearance based on the provided LineConfig."""

        if line_id is None:
            return

        line = self._lines.get(line_id, None)
        if line:
            line.set_color(config.color)
            line.set_linewidth(config.line_width)
            line.set_linestyle(config.line_style)
            line.set_marker(config.marker)
            line.set_markersize(config.marker_size)
            line.set(alpha=config.alpha)
            line.set(label=config.label)

        self.draw()

    def apply_axes_config(self, ax_id: str, plot_config: AxesConfig):
        """
        Applies general plot configurations (e.g., grid visibility).
        """
        ax = self._axes.get(ax_id, self.axes)

        ax.set_title(plot_config.title)
        ax.set_xlabel(plot_config.x_label)
        ax.set_ylabel(plot_config.y_label)

        if plot_config.show_legend:
            ax.legend(loc=plot_config.legend_loc) 

        else:
            ax.legend().set_visible(False)
        
        ax.grid(plot_config.show_grid)

        ax.set_xscale(plot_config.x_scale)
        ax.set_yscale(plot_config.y_scale)

        if plot_config.x_limits:
            ax.set_xlim(plot_config.x_limits)

        if plot_config.y_limits:
            ax.set_ylim(plot_config.y_limits)

        if plot_config.tight_layout:
            self.fig.tight_layout()

        else:
            self.fig.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
        
        self.draw()


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    fit_x = [0, 1, 2, 3, 4, 5]
    fit_y = [0, 1, 4, 9, 16, 25]

    fit_x_2 = [0, 1, 2, 3, 4, 5]
    fit_y_2 = [0, 1, 8, 27, 64, 125]

    app = QApplication(sys.argv)
    canvas = MplCanvas()
    canvas.add_fit_line(fit_x, fit_y)
    canvas.add_fit_line(fit_x_2, fit_y_2)
    canvas.show()

    sys.exit(app.exec_())