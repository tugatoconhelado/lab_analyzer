from PyQt5.QtCore import QObject
from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtCore import pyqtSlot as Slot
import numpy as np
import src.core.engine as engine
from src.core.engine import InspectInfo, DataResult


class AnalyzerBridge(QObject):
    """ 
    """
    imported_data_sig = Signal(dict)
    preview_data_sig = Signal(DataResult)
    inspect_info_sig = Signal(InspectInfo)
    data_sig = Signal(DataResult, DataResult)
    fit_data_sig = Signal(np.ndarray, np.ndarray)
    params_sig = Signal(list)
    residuals_sig = Signal(np.ndarray, np.ndarray)
    fit_report_sig = Signal(str)


    def __init__(self, engine, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._engine = engine

    @Slot()
    def get_models(self):
        """
        Grabs the list of models and parameters from the model_manager
        """
        models = self._engine.load_models()
        return models

    @Slot(str)
    def set_model(self, model_name: str):
        """
        Called when the user selects a model in the GUI dropdown.
        """
        model_params = self._engine.select_model(model_name)
        self.params_sig.emit(model_params)
        return model_params

    @Slot(str)
    def import_hdf5_data(self, filepath):

        structure = self._engine.load_file(filepath)
        self.imported_data_sig.emit(structure)

    @Slot(str)
    def fetch_inspect_info(self, path):

        info = self._engine.get_info(path)
        self.inspect_info_sig.emit(info)

    @Slot(str)
    def fetch_preview_data(self, path):
        
        data = self._engine.get_data(path)
        if isinstance(data, DataResult):
            self.preview_data_sig.emit(data)

    @Slot(str, str)
    def fetch_data(self, x_path: str, y_path: str):

        x_data, y_data = self._engine.select_data(x_path, y_path)
        self.data_sig.emit(
            x_data, y_data
        )

    @Slot()
    def perform_fit(self):

        result, fitted_params = self._engine.run_fit()
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

        params = self._engine.guess_params()
        self.params_sig.emit(params)

    def save_data(self):

        pass