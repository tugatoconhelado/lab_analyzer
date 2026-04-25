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
from src.controller.plot_manager import PlotManager


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
    models_sig = Signal(list)
    refresh_registry_sig = Signal(dict)


    def __init__(self, ui=None):
        super().__init__()

        self.ui = ui
        self.kernel_manager = QtInProcessKernelManager()
        self.kernel_manager.start_kernel()
        self.kernel_client = self.kernel_manager.client()
        self.kernel_client.start_channels()

        self.registry = WorkbenchRegistry(self.kernel_manager.kernel.shell)
        self.engine = AnalysisEngine(plugin_path=r"models", registry=self.registry)
        self.plot_manager = PlotManager(self.registry)
        self.ui.connect_to_bridge(self) # type: ignore
        self.connect_workbench_explorer()

    def connect_workbench_explorer(self):

        explorer = self.ui.workspace.workbench
        explorer.create_plot_sig.connect(self.create_plot)

    def get_kernel_client(self):
        return self.kernel_client
    
    def get_kernel_manager(self):
        return self.kernel_manager
    
    def create_plot(self, traces):

        self.plot_manager.create_new_window(traces)

    @Slot()
    def get_models(self):
        """
        Grabs the list of models and parameters from the model_manager
        """
        models = self.engine.read_available_models()
        print(f"Loaded models: {models}")
        self.models_sig.emit(models)

    @Slot(str)
    def set_model(self, model_name: str):
        """
        Called when the user selects a model in the GUI dropdown.
        """
        model_params = self.engine.select_model(model_name)
        print(f"Loaded model '{model_name}' with parameters: {model_params}")
        self.params_sig.emit(model_params)

    @Slot(str)
    def import_hdf5_data(self, filepath):

        structure = self.engine.load_file_structure(filepath)
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

        self.engine.load_dataset(data_path)

    @Slot(str, str, str)
    def run_fit(self, x_key: str, y_key: str, model_name: str):

        x_data, y_data = self.engine.select_data(x_key, y_key)

        if self.engine.active_model is None:
            raise ValueError("No model selected for fitting.")
        if self.engine.active_model.model_name != model_name:
            self.engine.select_model(model_name)

        fit_result, fitted_params = self.engine.run_fit()
        print("Fit result:", fit_result)
        print("Fitted parameters:", fitted_params)
        # if result or fitted_params is None:
        #     raise ValueError("Fit failed or returned no parameters.")
        
        fit_x_data = fit_result.trace.x
        fitted_data = fit_result.curve.data
        residuals = fit_result.residuals.data
        report = fit_result.report

        self.data_sig.emit(x_data, y_data)
        self.fit_data_sig.emit(fit_x_data, fitted_data)
        self.params_sig.emit(fitted_params)
        self.residuals_sig.emit(fit_x_data, residuals)
        self.fit_report_sig.emit(report)

    @Slot(str, str)
    def guess_parameters(self, x_key: str, y_key: str):

        x_data, y_data = self.engine.select_data(x_key, y_key)
        params = self.engine.guess_params()
        self.params_sig.emit(params)

    def save_data(self):

        pass

if __name__ == "__main__":
    bridge = AnalyzerBridge()