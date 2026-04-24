import os
import sys

from PyQt5.QtWidgets import QAbstractButton, QWidget, QButtonGroup, QFileDialog, QHBoxLayout, QLabel, QTreeWidgetItem, QHeaderView, QMenu
from PyQt5.QtCore import QRectF, Qt, QPoint
from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtCore import pyqtSlot as Slot
import pyqtgraph as pg
import numpy as np
import logging
logger = logging.getLogger(__name__)

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from src.core.structures import InspectInfo, Dataset
from resources.ui.ui_file_preview import Ui_Form


class FilePreviewer(QWidget, Ui_Form):

    request_preview_sig = Signal(str)
    request_inspect_info_sig = Signal(str)
    request_current_item_path = Signal()


    def __init__(self, parent=None):
        super().__init__(parent)

        self.setupUi(self)
        self._setup_preview_toggle()
        self._setup_plots()

    def _setup_preview_toggle(self):
        """
        Configures the toggle buttons for switching between
        the data preview and inspection views, and applies custom styling.
        """

        logger.debug("Setting up preview toggle buttons and styles.")
        self.toggleGroup = QButtonGroup(self)
        self.toggleGroup.addButton(self.display_button, 0) # ID 0
        self.toggleGroup.addButton(self.inspect_button, 1) # ID 1
        self.toggleGroup.setExclusive(True) # Only one can be pressed

        # Set the default state (Preview active)
        self.inspect_button.setChecked(True)

        self.toggleGroup.buttonClicked.connect(self._on_toggle_clicked)
        self._apply_segmented_style()

    def _setup_plots(self):
        """
        Initializes the preview plots for both 1D and 2D data.

        This method sets up a line plot for 1D data and an image plot for 2D data,
        along with a colorbar for the image plot.
        """

        logger.debug("Initializing preview plots for 1D and 2D data.")
        self.preview_dataline = self.data_preview_plot.plot([], pen="yellow")

        rect = QRectF(0, 0, 1, 1)

        self.heatmap.getViewBox().setAspectLocked(True)

        self.image_item = pg.ImageItem(axisOrder='row-major')
        self.image_item.setImage(np.zeros((10, 10)))
        self.image_item.setRect(rect)

        self.heatmap.addItem(self.image_item)
        self.colorbar = self.heatmap.addColorBar(
            self.image_item, colorMap=pg.colormap.getFromMatplotlib('inferno')
        )

    @Slot(QAbstractButton)
    def _on_toggle_clicked(self, button):
        """
        Slot that handles toggle button clicks and updates the preview panel.

        If the "Inspect" button is clicked, it switches to the inspection view.
        If the "Preview" button is clicked, it emits a signal to request a 
        data preview for the currently selected file in the tree.

        Parameters
        ----------
        button : QPushButton
            The button that was clicked, used to determine which view to show.

        Notes
        -----
        This method emits the `request_preview_sig` signal with the file path
        when the preview button is clicked, allowing the main application to 
        handle loading and displaying the preview.
        """
        if button == self.inspect_button:
            self.preview_index = 2
            self.preview_stackedwidget.setCurrentIndex(self.preview_index)
        else:
            self.request_current_item_path.emit()

    def update_preview_state(self, path, kind, shape):

        if self.inspect_button.isChecked() or kind == "Group" or not shape:
            self.request_inspect_info_sig.emit(path)

        elif self.display_button.isChecked() and kind == "Dataset" and shape:
            self.request_preview_sig.emit(path)

    def _apply_segmented_style(self):
        """
        Applies custom CSS styling to the toggle buttons 
        to create a segmented control appearance.

        This method reads a stylesheet that styles the toggle buttons to 
        look like a cohesive segmented control, with specific colors, borders,
        and rounded corners. It then applies this stylesheet to the toggle
        frame and forces a style update to ensure the new styles take effect.

        The stylesheet is expected to be located at 
        'resources/styles/toggle_style.qss'
        """
        qss_path = os.path.join('resources', 'styles', 'toggle_style.qss')
        with open(qss_path, 'r') as f:
            toggle_style = f.read()
        self.toggle_frame.setStyleSheet(toggle_style)
        self.toggle_frame.style().unpolish(self.toggle_frame)
        self.toggle_frame.style().polish(self.toggle_frame)
        self.toggle_frame.update()

    @Slot(InspectInfo)
    def update_inspect_info(self, info: InspectInfo):
        """
        Updates the inspection view with the provided information about the selected item.
        
        This method takes an `InspectInfo` object containing details about
        the selected HDF5 item (such as its path, name, type, shape, and 
        attributes) and populatesthe inspection layout with this information.
        It clears any existing widgets in the inspection layout before adding
        new labels and information based on the type of the item.
        
        Parameters
        ----------
        info : InspectInfo
            A dataclass containing information about the selected HDF5 item,
            including its path, name, type, shape, and attributes.

        Notes
        -----
        This method dynamically creates labels and layouts to display the information in a
        structured way, and it switches the preview to the inspection view when called.
        """

        self._clear_inspect_layout()

        kind = "Dataset" if info.is_dataset else "Group"
        kind_layout = QHBoxLayout()
        kind_label = QLabel(kind)
        kind_label.setStyleSheet("font-size: 10pt;")
        kind_layout.addWidget(kind_label)
        kind_layout.setContentsMargins(0, 5, 0, 5)
        self.inspect_layout.addRow(kind_layout)
        
        self.inspect_layout.addRow("Path", QLabel(info.path))
        self.inspect_layout.addRow("Name", QLabel(info.name))

        if info.is_dataset:
            if info.dtype is None:
                raise ValueError(f"Dataset at path '{info.path}' is missing dtype information.")    
            self.inspect_layout.addRow("Shape", QLabel(str(info.shape)))
            dtype = info.dtype + ", " + str(info.size_bytes) + ", " + str(info.byte_order)
            self.inspect_layout.addRow("Type", QLabel(dtype))

        if info.attributes:
        
            attr_layout = QHBoxLayout()
            attr_label = QLabel("Attributes")
            attr_label.setStyleSheet("font-size: 10pt;")
            attr_layout.addWidget(attr_label)
            attr_layout.setContentsMargins(0, 5, 0, 5)
            self.inspect_layout.addRow(attr_layout)

            for key, value in info.attributes.items():
                self.inspect_layout.addRow(key, QLabel(str(value)))

        self.preview_index = 2
        self.inspect_button.click()

    def _clear_inspect_layout(self):
        """Removes all widgets from the inspect layout."""
        while self.inspect_layout.rowCount() > 0:
            self.inspect_layout.removeRow(0)

    @Slot(Dataset)
    def update_preview_plot(self, data: Dataset):
        """
        Updates the preview plot based on the provided data.
        
        This method takes a `Dataset` object containing the data to be 
        previewed and updates the appropriate plot (line plot for 1D data,
        image plot for 2D/3D data). It checks the dimensionality of the data
        and updates the preview accordingly. For 1D data, it updates the line
        plot. For 2D data, it updates the image plot, and for 3D data, it 
        takes the first channel and updates the image plot.

        Parameters
        ----------
        data : Dataset
            A dataclass containing the data to be previewed, including its dimensionality and the actual
            data array.

        Notes
        -----
        This method also switches the view according to the data when called.
        """
        if data.ndim == 1:
            self.preview_index = 0
            self.preview_dataline.setData(data.data)
        elif data.ndim == 2:
            self.preview_index = 1
            self._update_preview_img(data.data)
        elif data.ndim == 3:
            self.preview_index = 1
            self._update_preview_img(data.data[:, :, 0])

        self.preview_stackedwidget.setCurrentIndex(self.preview_index)

    def _update_preview_img(self, img: np.ndarray):
        """Updates the image plot with the provided 2D data array."""

        self.image_item.setImage(np.flip(img, 0))
        self.colorbar.setLevels((np.min(img), np.max(img)))



if __name__ == '__main__':

    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    previewer = FilePreviewer()
    previewer.show()
    sys.exit(app.exec())