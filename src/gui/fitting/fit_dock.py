from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDockWidget, QTableWidgetItem)
from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtCore import pyqtSlot as Slot
from PyQt5.uic import loadUi

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from src.core.structures import LineConfig, AxesConfig


class FitDock(QDockWidget):
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

    def __init__(self, parent=None):
        super().__init__(parent)
        loadUi(
            os.path.join('resources', 'ui', 'fit_dock.ui'), self
        )

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

    def select_model(self, model):
        """Emits the select_model_sig with the selected model name."""
        self.select_model_sig.emit(model)

    @Slot(list)
    def refresh_models(self, models: list):
        """Refreshes the model selection dropdown with a new list of models."""

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
            self.parameters_table.setItem(0, 1, name_item)
            
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




if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    widget = FitDock()
    widget.show()
    sys.exit(app.exec())