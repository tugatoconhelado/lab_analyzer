from PyQt5.QtCore import QObject
from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtCore import pyqtSlot as Slot
import numpy as np
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.core.engine import AnalysisEngine
from src.core.engine import InspectInfo, Dataset
from src.core.workbench import WorkbenchRegistry
from qtconsole.inprocess import QtInProcessKernelManager


class AnalyzerBridge(QObject):
    """ 
    """
    imported_data_sig = Signal(dict)
    preview_data_sig = Signal(Dataset)
    inspect_info_sig = Signal(InspectInfo)
    data_sig = Signal(Dataset, Dataset)
    fit_data_sig = Signal(np.ndarray, np.ndarray)
    params_sig = Signal(list)
    residuals_sig = Signal(np.ndarray, np.ndarray)
    fit_report_sig = Signal(str)


    def __init__(self):
        super().__init__()

        self.kernel_manager = QtInProcessKernelManager()
        self.kernel_manager.start_kernel()
        self.kernel_client = self.kernel_manager.client()
        self.kernel_client.start_channels()

        self.registry = WorkbenchRegistry(self.kernel_manager.kernel.shell)
        self.engine = AnalysisEngine(plugin_path="", registry=self.registry)

    def get_kernel_client(self):
        return self.kernel_client
    
    def get_kernel_manager(self):
        return self.kernel_manager

    @Slot()
    def get_models(self):
        """
        Grabs the list of models and parameters from the model_manager
        """
        models = self.engine.load_models()
        return models

    @Slot(str)
    def set_model(self, model_name: str):
        """
        Called when the user selects a model in the GUI dropdown.
        """
        model_params = self.engine.select_model(model_name)
        self.params_sig.emit(model_params)
        return model_params

    @Slot(str)
    def import_hdf5_data(self, filepath):

        structure = self.engine.load_file(filepath)
        self.imported_data_sig.emit(structure)

    @Slot(str)
    def fetch_inspect_info(self, path):

        info = self.engine.get_info(path)
        self.inspect_info_sig.emit(info)

    @Slot(str)
    def fetch_preview_data(self, path):
        
        data = self.engine.get_preview_data(path)
        if isinstance(data, Dataset):
            self.preview_data_sig.emit(data)

    @Slot(str)
    def fetch_data(self, data_path: str):

        self.engine.get_data(data_path)

    @Slot()
    def perform_fit(self):

        result, fitted_params = self.engine.run_fit()
        if result or fitted_params is None:
            raise ValueError("Fit failed or returned no parameters.")
        
        x_data = result.userkws['x']
        fitted_data = result.best_fit
        residuals = result.residual
        report = result.fit_report()

        self.fit_data_sig.emit(x_data, fitted_data)
        self.params_sig.emit(fitted_params)
        self.residuals_sig.emit(x_data, residuals)
        self.fit_report_sig.emit(report)

    @Slot()
    def guess_parameters(self):

        params = self.engine.guess_params()
        self.params_sig.emit(params)

    def save_data(self):

        pass

if __name__ == "__main__":
    bridge = AnalyzerBridge()