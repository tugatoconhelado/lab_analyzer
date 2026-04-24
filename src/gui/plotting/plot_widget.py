from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtCore import pyqtSlot as Slot
from matplotlib.backends.backend_qt import NavigationToolbar2QT
import numpy as np
import pyqtgraph as pg
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from src.core.structures import InspectInfo, Dataset, LineConfig
from src.gui.plotting.mpl_canvas import MplCanvas
from resources.ui.ui_plot_widget import Ui_plot_window

class PlotWidget(QMainWindow, Ui_plot_window):

    
    def __init__(self, parent=None, plot_id="Data Plot 0"):
        super().__init__(parent)
        self.setupUi(self)
        self.plot_id = plot_id

        self.plot_canvas = MplCanvas(self)
        self.toolbar = NavigationToolbar2QT(self.plot_canvas, self)
        
        self.mpl_plot_layout.addWidget(self.toolbar)
        self.mpl_plot_layout.addWidget(self.plot_canvas)

        self.line_configs = {}  # Store LineConfig objects by line name



if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    widget = PlotWidget(plot_id="My Plot")
    widget.show()
    sys.exit(app.exec())