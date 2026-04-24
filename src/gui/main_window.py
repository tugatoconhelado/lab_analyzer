from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtCore import pyqtSlot as Slot
from PyQt5.uic import loadUi

import numpy as np
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.core.structures import Dataset, LineConfig
from src.gui.bridge import AnalyzerBridge
from src.gui.plotting.plot_config import PlotControlDock
from src.gui.plotting.plot_widget import PlotWidget
from src.core.style_generator import LineType
from src.gui.file_explorer import FileExplorerDock
from src.gui.fitting.fit_dock import FitDock
from src.gui.console.workspace import WorkspaceWidget
from src.gui.file_loader.hdf5_explorer import HDF5ExplorerDock
from src.gui.log_registry.log_registry import LogRegistryDock



class AnalyzerMainWindow(QMainWindow):
    """
    Main Window of the Analyzer software
    """

    def __init__(self, bridge: AnalyzerBridge, *args, **kwargs):
        super().__init__(*args, **kwargs)

        loadUi(
            os.path.join('resources', 'ui', 'analyzer.ui'), self
        )

        self._bridge = bridge
        self.plot_counter = 0
        self._open_plots = {}

        self.preview_index = 2
        self.axis_options_path = {}

        self._setup_console()
        self._setup_hdf5_explorer()
        self._setup_file_explorer()
        self._setup_fit_dock()
        self._setup_plot_config()
        self._setup_log_registry()
        self.create_new_plot("Initial Plot")

    def connect_to_bridge(self):

        self.hdf5_explorer.connect_to_bridge(self._bridge)        
        self._bridge.data_sig.connect(
            self.plot_data
        )
        
        self.workspace.connect_to_bridge(self._bridge)
        self.workspace.console.push_to_console({'hub': self.workspace})  # Expose the workspace to the console as 'hub'

        self.fit_dock.connect_to_bridge(self._bridge)
        self._bridge.fit_data_sig.connect(
            self.plot_fit_data
        )
        self._bridge.residuals_sig.connect(
            self.plot_fit_residuals
        )

        self.file_explorer.connect_to_bridge(self._bridge)

    def _setup_log_registry(self):
        self.log_registry = LogRegistryDock(parent=self)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.log_registry)

    def _setup_console(self):
        """"
        Sets up the Jupyter console and variable explorer,
        and connects them to an in-process kernel.
        """

        kernel_manager = self._bridge.get_kernel_manager()
        kernel_client = self._bridge.get_kernel_client()
        self.workspace = WorkspaceWidget(self, kernel_manager, kernel_client)
        self.setCentralWidget(self.workspace)

    def _setup_hdf5_explorer(self):
        
        self.hdf5_explorer = HDF5ExplorerDock(parent=self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.hdf5_explorer)

    def _setup_fit_dock(self):

        self.fit_dock = FitDock(parent=self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.fit_dock)
        self.tabifyDockWidget(self.file_explorer, self.fit_dock)
        self.file_explorer.raise_()

    def _setup_file_explorer(self):

        self.file_explorer = FileExplorerDock("File Explorer", parent=self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.file_explorer)
        
    def _setup_plot_config(self):

        self.config_widget = PlotControlDock(parent=self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.config_widget)
        self.config_widget.line_config_changed.connect(self.update_plot_config)
        self.tabifyDockWidget(self.fit_dock, self.config_widget)

    def create_new_plot(self, title="New Plot"):

        self.plot_counter += 1
        plot = PlotWidget(plot_id=f"Data Plot {self.plot_counter}", parent=self)
        self._open_plots[plot.plot_id] = plot
        plot.setWindowTitle(title)
        plot.show()
        plot.raise_()

    @Slot(str, LineConfig)
    def update_plot_config(self, line: str, config: LineConfig):

        plot = list(self._open_plots.values())[0]
        plot.plot_canvas.apply_line_config(line, config)

    @Slot(Dataset, Dataset)
    def plot_data(self, x_data, y_data):

        plot = list(self._open_plots.values())[0]
        line_id = plot.plot_canvas.add_data_line(x_data, y_data)
        fit_config = self.config_widget.add_line_config(line_id, LineType.RAW_DATA)
        plot.plot_canvas.apply_line_config(line_id, fit_config)

    @Slot(np.ndarray, np.ndarray)
    def plot_fit_data(self, x_data, fit_data):

        plot = list(self._open_plots.values())[0]
        line_id = plot.plot_canvas.add_fit_line(x_data, fit_data)
        fit_config = self.config_widget.add_line_config(line_id, LineType.FIT_CURVE)
        plot.plot_canvas.apply_line_config(line_id, fit_config)

    @Slot(np.ndarray, np.ndarray)
    def plot_fit_residuals(self, x_data, residuals):

        pass



if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    from src.gui.bridge import AnalyzerBridge

    app = QApplication(sys.argv)
    
    class MockBridge:
        def request_load(self, p): print(f"Mock loading: {p}")
        
    window = AnalyzerMainWindow(bridge=MockBridge())  # type: ignore
    window.show()

    data = {
        'pl_mean': np.random.random(100),
        'pl_raw_mean': np.random.random((10, 10, 2)),
        'pl_raw_std': np.random.random((10, 10, 2)),
        'pl_std': np.random.random(100),
        'tau': np.random.random(100)
    }
    metadata = {'iterations': 30, 'loop': 10000, 'repeat_exp': 10, 'sequence': 'T1laser'}
    general = {
        'column_dtypes': np.array([b'float64', b'float64', b'float64', b'float64', b'float64'], dtype='|S7'),
        'column_headers': np.array(['tau', 'pl_raw_mean', 'pl_raw_std', 'pl_mean', 'pl_std'], dtype=object),
        'notes': 'This are some notes',
        'steps': np.array([10, 30]),
        'timestamp': '2026-04-09T13:58:15.277085'
    }

    
    #window.hdf5_explorer.update_imported_data_tree(tree)
    #window.create_new_plot("Test Plot")
    sys.exit(app.exec())
