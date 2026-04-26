from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtCore import pyqtSlot as Slot
from PyQt5.QtCore import QTimer
from matplotlib.backends.backend_qt import NavigationToolbar2QT
import numpy as np
import pyqtgraph as pg
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from src.core.plot_object import PlotObject
from src.gui.plotting.mpl_canvas import MplCanvas
from resources.ui.ui_plot_widget import Ui_plot_window


class PlotWindow(QMainWindow, Ui_plot_window):

    
    def __init__(self, parent=None, plot_obj: PlotObject | None = None, plot_name="Plot 00"):
        super().__init__(parent)
        self.setupUi(self)
        self.plot_name = plot_name
        self.plot_obj = plot_obj or PlotObject(plot_name=plot_name, registry=None)

        self.plot_canvas = MplCanvas(self)
        self.toolbar = NavigationToolbar2QT(self.plot_canvas, self)
        
        self.mpl_plot_layout.addWidget(self.toolbar)
        self.mpl_plot_layout.addWidget(self.plot_canvas)

        self.line_configs = {}  # Store LineConfig objects by line name

        self.setWindowTitle(f"Q-DART Plot - {self.plot_name}")

    def refresh(self):
        self.plot_canvas.update_from_object(self.plot_obj)

    def showEvent(self, a0):
        super().showEvent(a0)
        # Queue activation after show so window managers apply focus reliably.
        QTimer.singleShot(0, self._bring_to_front)

    def _bring_to_front(self):
        self.raise_()
        self.activateWindow()




if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    widget = PlotWindow(plot_name="My Plot")
    widget.show()
    sys.exit(app.exec())