from PyQt5.QtWidgets import QWidget

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from src.core.structures import LineConfig, AxesConfig


class MplCanvas(FigureCanvasQTAgg):


    def __init__(self, parent=None, width=5, height=4, dpi=100):

        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        self._lines = {}
        self._fit_line_counter = 0
        self._data_line_counter = 0
        
        # Initialize the canvas
        super().__init__(self.fig)
        self.setParent(parent)

    def clear_plot(self):
        """Clears the current plot and resets line tracking."""
        self.axes.clear()
        self._lines.clear()
        self._fit_line_counter = 0
        self._data_line_counter = 0
        self.draw()

    def add_data_line(self, x_data, y_data):
        """Standard method to refresh the plot with new DataResult."""
        line = self.axes.plot(x_data.data, y_data.data, 'o', color='blue', label="Data")[0]
        self.axes.set_ylabel(f"{y_data.name}")
        self.axes.set_xlabel(f"{x_data.name}")
            
        self.axes.set_title(f"Dataset: {y_data.path.split('/')[-1]}")
        
        self.draw()

        if "data" in self._lines:
            line_id = f"data_{self._data_line_counter:02d}"
        else:
            line_id = "data"
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

    def apply_line_config(self, line_id: str, config: LineConfig):
        """Updates the plot's appearance based on the provided LineConfig."""

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

    def apply_plot_config(self, plot_id: str, plot_config: AxesConfig):
        """
        Applies general plot configurations (e.g., grid visibility).
        """
        self.axes.set_title(plot_config.title)
        self.axes.set_xlabel(plot_config.x_label)
        self.axes.set_ylabel(plot_config.y_label)

        self.axes.legend(loc=plot_config.legend_loc) if plot_config.show_legend else self.axes.legend().set_visible(False)
        self.axes.grid(plot_config.show_grid)

        self.axes.set_xscale(plot_config.x_scale)
        self.axes.set_yscale(plot_config.y_scale)
        if plot_config.x_limits:
            self.axes.set_xlim(plot_config.x_limits)
        if plot_config.y_limits:
            self.axes.set_ylim(plot_config.y_limits)
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

    print(canvas._lines)
    sys.exit(app.exec_())