from PyQt5.QtWidgets import QDockWidget, QColorDialog, QLabel
from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtCore import pyqtSlot as Slot

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from src.core.structures import LineConfig, AxesConfig
from src.core.style_generator import get_default_config, LineType
from resources.ui.ui_plot_dock import Ui_plot_dock

class PlotControlDock(QDockWidget, Ui_plot_dock):
    

    line_config_changed = Signal(str, LineConfig)
    plot_config_changed = Signal(str, AxesConfig)


    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        
        self._line_configs = {}
        self._plot_configs = {} 
        self.is_updating_ui = False  # Flag to prevent recursive updates

        self._LINE_STYLES = {
            "Solid": "-",
            "Dashed": "--",
            "Dotted": ":",
            "Dash-dot": "-."
        }
        self._MARKERS = {
            "Circle": "o",
            "Square": "p",
            "Triangle Up": "^",
            "Triangle Down": "v",
            "Triangle Left": "<",
            "Triangle Right": ">",
            "Diamond": "h",
            "Cross": "x",
            "Plus": "+",
            "None": "",
        }

        
        self.line_buttonbox.clicked.connect(self.process_button_click)
        self.pick_color_button.clicked.connect(self.pick_color)
        self.plot_line_combobox.currentTextChanged.connect(self.on_line_selection_changed)

        self.plot_combobox.currentTextChanged.connect(self._switch_plot)
        self.plot_buttonbox.clicked.connect(self.process_plot_button_click)

        self.setup_styles()

    def setup_styles(self):
        self.line_style_combobox.clear()
        self.line_style_combobox.addItems(list(self._LINE_STYLES.keys()))
        self.marker_combobox.clear()
        self.marker_combobox.addItems(list(self._MARKERS.keys()))

    def pick_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.color_edit.setText(color.name())
            self.color_label.setStyleSheet(f"background-color: {color.name()}")

    def _switch_plot(self, plot_id):
        plot_id = self.plot_combobox.currentText()
        if plot_id in self._plot_configs:
            plot_config = self._plot_configs[plot_id]
            self.update_ui_from_plot_config(plot_id, plot_config)

    def update_ui_from_plot_config(self, plot_id, plot_config: AxesConfig):
        self.is_updating_ui = True

        # Content
        self.title_edit.setText(plot_config.title)
        self.x_label_edit.setText(plot_config.x_label)
        self.y_label_edit.setText(plot_config.y_label)
        self.legend_checkbox.setChecked(plot_config.show_legend)
        self.grid_checkbox.setChecked(plot_config.show_grid)

        # Scaling
        self.x_scale_combobox.setCurrentText(plot_config.x_scale)
        self.y_scale_combobox.setCurrentText(plot_config.y_scale)
        if plot_config.x_limits:
            self.x_min_spinbox.setValue(plot_config.x_limits[0])
            self.x_max_spinbox.setValue(plot_config.x_limits[1])
        else:
            self.x_min_spinbox.setValue(0)
            self.x_max_spinbox.setValue(1)
        if plot_config.y_limits:
            self.y_min_spinbox.setValue(plot_config.y_limits[0])
            self.y_max_spinbox.setValue(plot_config.y_limits[1])
        else:
            self.y_min_spinbox.setValue(0)
            self.y_max_spinbox.setValue(1)
        
        # General
        self.tight_layout_checkbox.setChecked(plot_config.tight_layout)
        self.sci_not_checkbox.setChecked(plot_config.use_sci_notation)
        self.legend_loc_combobox.setCurrentText(plot_config.legend_loc)

        self.is_updating_ui = False

    def process_plot_button_click(self, button):
        
        if button.text() == "Apply":
            self.emit_plot_config_change()

        elif button.text() == "Reset":
            raise NotImplementedError("Reset functionality not implemented yet.")
        
        elif button.text() == "Help":
            raise NotImplementedError("Help functionality not implemented yet.")

    def process_button_click(self, button):
        
        if button.text() == "Apply":
            self.emit_line_config_change()

        elif button.text() == "Reset":
            raise NotImplementedError("Reset functionality not implemented yet.")
        
        elif button.text() == "Help":
            raise NotImplementedError("Help functionality not implemented yet.")

    def emit_line_config_change(self):

        line_name = self.plot_line_combobox.currentText()
        if line_name not in self._line_configs:
            return
        config = self._line_configs[line_name]

        config.label = self.label_edit.text()
        config.color = self.color_edit.text()
        line_style = self.line_style_combobox.currentText()
        config.line_style = self._LINE_STYLES.get(line_style, "-")
        config.line_width = self.line_width_spinbox.value()
        marker = self.marker_combobox.currentText()
        config.marker = self._MARKERS.get(marker, "o")
        config.marker_size = self.marker_size_spinbox.value()
        config.alpha = self.alpha_spinbox.value()

        self.line_config_changed.emit(line_name, config)

    def emit_plot_config_change(self):

        plot_id = self.plot_combobox.currentText()
        if plot_id not in self._plot_configs:
            return
        config = self._plot_configs[plot_id]

        config.title = self.title_edit.text()
        config.x_label = self.x_label_edit.text()
        config.y_label = self.y_label_edit.text()
        config.show_legend = self.legend_checkbox.isChecked()
        config.show_grid = self.grid_checkbox.isChecked()
        config.x_scale = self.x_scale_combobox.currentText()
        config.y_scale = self.y_scale_combobox.currentText()
        config.x_limits = (self.x_min_spinbox.value(), self.x_max_spinbox.value())
        config.y_limits = (self.y_min_spinbox.value(), self.y_max_spinbox.value())
        config.tight_layout = self.tight_layout_checkbox.isChecked()
        config.use_sci_notation = self.sci_not_checkbox.isChecked()
        config.legend_loc = self.legend_loc_combobox.currentText()

        self.plot_config_changed.emit(plot_id, config)

    def add_line_config(self, line_name, line_type: str, default_config=None):
        """Call this from the Engine/MainWindow when a fit or new data is added."""
        if line_name not in self._line_configs:
            if default_config is None:
                default_config = get_default_config(line_name, line_type)
            self._line_configs[line_name] = default_config
            self.plot_line_combobox.addItem(line_name)
        
        # Automatically select the newly added line
        self.plot_line_combobox.setCurrentText(line_name)
        return self._line_configs[line_name]

    def on_line_selection_changed(self):
        line_id = self.plot_line_combobox.currentText() # This is the internal ID
        if line_id in self._line_configs:
            config = self._line_configs[line_id]
            
            self.is_updating_ui = True
            self.update_ui_from_config(config)

            self.is_updating_ui = False

    def update_ui_from_config(self, config):

        self.label_edit.setText(config.label)
        self.color_edit.setText(config.color)
        self.color_label.setStyleSheet(f"background-color: {config.color}")
        self.line_style_combobox.setCurrentText(config.line_style)
        self.line_width_spinbox.setValue(config.line_width)
        self.marker_combobox.setCurrentText(config.marker)
        self.marker_size_spinbox.setValue(config.marker_size)
        self.alpha_spinbox.setValue(config.alpha)



if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    from matplotlib import markers

    #print(markers.MarkerStyle.markers)
    app = QApplication(sys.argv)
    widget = PlotControlDock()
    widget.show()
    sys.exit(app.exec())