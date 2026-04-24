from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDockWidget, QTableWidgetItem)
from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtCore import pyqtSlot as Slot

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from src.core.structures import LineConfig, AxesConfig
from resources.ui.ui_fit_dock import Ui_fit_dock

class FitDock(QDockWidget, Ui_fit_dock):
    """
    Dock widget for displaying fit results and allowing parameter adjustments.
    
    Attributes
    ----------
    parameters_table : QTableWidget
        A table widget that lists fit parameters, their values, and 
        whether they are fixed.
    fit_report_label : QLabel
        A label that displays the fit report, including statistics and 
        parameter values.
    select_model_sig : Signal
        A signal emitted when the user selects a different model from the 
        dropdown, carrying the model name as a string.
    request_models_sig : Signal
        A signal emitted when the user clicks the refresh button to request an
        updated list of available models.
    
    Methods
    -------
    update_parameters_table(params)
        Updates the parameters table with the given list of parameter 
        dictionaries.
    update_fit_report(report)
        Updates the fit report label with the provided report string.
    select_model(model)
        Emits the select_model_sig with the selected model name when the user 
        changes the selection in the model dropdown.
    """

    select_model_sig = Signal(str)
    request_models_sig = Signal()
    run_fit_sig = Signal(str, str, str)  # x_key, y_key, model_name
    guess_parameters_sig = Signal(str, str)  # x_key, y_key

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self._connect_gui_signals()

    def _connect_gui_signals(self):
        """
        Connects GUI signals to their slots for handling user interactions.

        This method sets up the connections for the model selection dropdown
        and the refresh button.
        """
        self.models_combobox.currentTextChanged.connect(self.select_model)
        self.refresh_button.clicked.connect(
            self.request_models_sig.emit
        )

    def connect_to_bridge(self, bridge):

        self.registry_ref = bridge.registry
        self.registry_ref.registry_changed.connect(
            self.refresh_selectors
        )

        # Managing fitting events
        self.fit_button.clicked.connect(
            self.handle_run_fit
        )
        self.run_fit_sig.connect(
            bridge.run_fit
        )
        bridge.fit_report_sig.connect(
            self.update_fit_report
        )

        # Model selection and parameter setting
        self.request_models_sig.connect(
            bridge.get_models
        )
        bridge.models_sig.connect(
            self.refresh_models
        )
        self.select_model_sig.connect(
            bridge.set_model
        )
        bridge.params_sig.connect(
            self.update_parameters_table
        )
        self.guess_button.clicked.connect(
            self.handle_guess_params
        )
        self.guess_parameters_sig.connect(
            bridge.guess_parameters
        )

    def select_model(self, model):
        """Emits the select_model_sig with the selected model name."""
        self.select_model_sig.emit(model)

    @Slot(list)
    def refresh_models(self, models: list):
        """Refreshes the model selection dropdown with a new list of models."""
        print(f"Received model list: {models}")
        self.models_combobox.clear()
        self.models_combobox.addItems(models)

    @Slot(list)
    def update_parameters_table(self, params):
        """
        Updates the parameters table with a given list of parameters

        Each parameter dictionary should contain keys like 
        'name', 'value', 'vary', 'min', and 'max'.

        Parameters
        ----------
        params : list of dict
            A list of parameter dictionaries, where each dictionary contains:
            - 'name': The name of the parameter (str)
            - 'value': The current value of the parameter (float)
            - 'vary': A boolean indicating whether the parameter is varied in the fit
            - 'min': The minimum allowed value for the parameter (float)
            - 'max': The maximum allowed value for the parameter (float)
        """

        self.parameters_table.setColumnCount(len(params))
        self.parameters_table.setRowCount(5)
        self.parameters_table.setVerticalHeaderLabels(
            ["Parameter", "Value", "Fixed", "Min", "Max"])
        for i, param in enumerate(params):
            # Column 0: Name   
            name_item = QTableWidgetItem(param["name"])
            self.parameters_table.setItem(0, i, name_item)
            
            # Column 1: Value (Editable)
            val_item = QTableWidgetItem(f"{param['value']:.4f}")
            self.parameters_table.setItem(1, i, val_item)
            
            # Column 2: Fixed Checkbox
            check_item = QTableWidgetItem()
            check_item.setCheckState(
                Qt.CheckState.Unchecked if param["vary"] else Qt.CheckState.Checked
            )
            self.parameters_table.setItem(2, i, check_item)
            
            # Column 3: Display min for reference
            min_item = QTableWidgetItem(f"{param['min']}")
            self.parameters_table.setItem(3, i, min_item)

             # Column 3: Display max for reference
            max_item = QTableWidgetItem(f"{param['max']}")
            self.parameters_table.setItem(4, i, max_item)

    @Slot(str)
    def update_fit_report(self, report):
        """
        Update the fit report label with the provided text.

        Parameters
        ----------
        report : str
            The text to display in the fit report label, typically containing 
            fit statistics and parameter values.
        """

        self.fit_report_label.setText(report)

    @Slot()
    def refresh_selectors(self):
        """Updates the dropdowns with current Registry keys."""
        # Save current selections so they don't reset to index 0 on every update
        current_x = self.x_combo.currentText()
        current_y = self.y_combo.currentText()

        self.x_combo.clear()
        self.y_combo.clear()
        
        # Get keys from the Registry warehouse
        keys = list(self.registry_ref._data_store.keys())
        self.x_combo.addItems(keys)
        self.y_combo.addItems(keys)

        # Restore previous selection if it still exists
        self.x_combo.setCurrentText(current_x)
        self.y_combo.setCurrentText(current_y)

    def handle_run_fit(self):
        """Emits the run_fit_sig with the selected x, y, and model."""
        x_key = self.x_combo.currentText()
        y_key = self.y_combo.currentText()
        model_name = self.models_combobox.currentText()
        self.run_fit_sig.emit(x_key, y_key, model_name)

    def handle_guess_params(self):
        """Emits the guess_parameters signal with the selected x and y keys."""
        x_key = self.x_combo.currentText()
        y_key = self.y_combo.currentText()
        self.guess_parameters_sig.emit(x_key, y_key)

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import numpy as np
    app = QApplication(sys.argv)
    widget = FitDock()
    widget.show()

    params = [
        {'name': 'T1', 'value': 55.5, 'stderr': 0.0, 'min': -np.inf, 'max': np.inf, 'vary': True},
        {'name': 'amplitude', 'value': 0.2, 'stderr': 0.0, 'min': -np.inf, 'max': np.inf, 'vary': True},
        {'name': 'background', 'value': 1.0, 'stderr': 0.0, 'min': -np.inf, 'max': np.inf, 'vary': True}
    ]
    widget.update_parameters_table(params)
    sys.exit(app.exec())