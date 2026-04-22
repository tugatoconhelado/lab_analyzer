import os
import sys

from PyQt5.QtWidgets import QAbstractButton, QDockWidget, QButtonGroup, QFileDialog, QHBoxLayout, QLabel, QTreeWidgetItem
from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtCore import pyqtSlot as Slot
from PyQt5.uic import loadUi
import pyqtgraph as pg
import numpy as np

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from src.core.structures import InspectInfo, DataResult



class HDF5ExplorerDock(QDockWidget):
    """
    A dockable widget for exploring HDF5 files, with a preview
    panel that can toggle between a data preview and an inspection view.

    Attributes
    ----------
    request_preview_sig : Signal
        A signal emitted when the user requests a data preview,
        carrying the file path.
    request_data_sig : Signal
        A signal emitted when the user selects axis data for plotting,
        carrying the paths of the selected x and y axis datasets.
    request_inspect_info_sig : Signal
        A signal emitted when the user requests inspection information for 
        an item, carrying the file path of the selected item.
    import_hdf5_sig : Signal
        A signal emitted when the user selects an HDF5 file to import,
        carrying the file path of the selected HDF5 file.
    axis_options_path : dict
        A dictionary mapping dataset names to their full HDF5 paths, used for
        populating the axis selection combo boxes and retrieving the correct 
        data when the user selects an axis option.
    preview_index : int
        An integer representing the current index of the preview stacked 
        widget, where different values correspond to the preview or inspection 
        views.
    
    Methods
    -------
    configure_preview_toggle()
        Sets up the toggle buttons for switching between 
        data preview and inspection views.
    _on_toggle_clicked(button: QPushButton)
        Slot that handles toggle button clicks and updates
        the preview accordingly.
    _apply_segmented_style()
        Applies custom CSS styling to the toggle buttons
        to create a segmented control appearance.
    """
    request_preview_sig = Signal(str)
    request_data_sig = Signal(str, str)
    request_inspect_info_sig = Signal(str)
    import_hdf5_sig = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        loadUi(
            os.path.join('resources', 'ui', 'hdf5_explorer.ui'), self
        )
        self.current_file = None
        self.possible_data_paths = [
            os.path.join(os.path.expanduser("~"), "Scripts", "data")
        ]
        self.axis_options_path = {}
        self.preview_index = 2
        self._setup_preview_toggle()
        self._setup_plots()
        self._connect_gui_signals()

    def _setup_preview_toggle(self):
        """
        Configures the toggle buttons for switching between
        the data preview and inspection views, and applies custom styling.
        """

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

    def _connect_gui_signals(self):
        """
        Connects GUI signals to their slots for handling user interactions.

        This method connects the toggle button clicks, tree selection changes,
        axis selection changes, and load button clicks to their corresponding
        handler methods.
        """

        self.imported_data_tree.currentItemChanged.connect(
            self._on_tree_selection_changed
        )
        self.x_axis_combobox.activated.connect(self._select_axis_data)
        self.y_axis_combobox.activated.connect(self._select_axis_data)
        self.load_button.clicked.connect(
            self._select_hdf5_file
        )

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
            current_tree_item = self.imported_data_tree.currentItem()
            if not current_tree_item:
                return
            path = current_tree_item.data(0, Qt.ItemDataRole.UserRole)["path"]
            if not path:
                return
            self.request_preview_sig.emit(path)

    @Slot(QTreeWidgetItem, QTreeWidgetItem)
    def _on_tree_selection_changed(self, current, previous):
        """
        Handles changes in the tree selection and updates 
        the preview/inspection view accordingly.
        
        When the user selects a different item in the tree, this method checks
        the type of the selected item (Group or Dataset) and whether it has a shape.
        Based on this information and the current toggle state, it decides whether
        to show the inspection view or request a data preview.
        
        Parameters
        ----------
        current : QTreeWidgetItem
            The currently selected tree item, used to determine the path and
            type of the selection.
        previous : QTreeWidgetItem
            The previously selected tree item, not used in this method but
            provided by the signal.
        Notes
        -----
        This method emits the `request_inspect_info_sig` signal with the file 
        path when the inspect button is active or when a group is selected,
        allowing the main application to handle loading and displaying the
        inspection information. It emits the `request_preview_sig` signal when
        the preview button is active and a dataset with shape is selected,
        allowing the main application to handle loading and displaying the
        data preview.
        """

        path = current.data(0, Qt.ItemDataRole.UserRole)["path"]
        kind = current.data(0, Qt.ItemDataRole.UserRole)["kind"]
        shape = current.data(0, Qt.ItemDataRole.UserRole).get("shape", False)
        if not path:
            return
        # Request inspect info to the logic
        if self.inspect_button.isChecked() or kind == "Group" or not shape:
            print("INFO")
            self.request_inspect_info_sig.emit(path)

        elif self.display_button.isChecked() and kind == "Dataset" and shape:
            print("PREVIEW")
            self.request_preview_sig.emit(path)

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

    @Slot(DataResult)
    def update_preview_plot(self, data: DataResult):
        """
        Updates the preview plot based on the provided data.
        
        This method takes a `DataResult` object containing the data to be 
        previewed and updates the appropriate plot (line plot for 1D data,
        image plot for 2D/3D data). It checks the dimensionality of the data
        and updates the preview accordingly. For 1D data, it updates the line
        plot. For 2D data, it updates the image plot, and for 3D data, it 
        takes the first channel and updates the image plot.

        Parameters
        ----------
        data : DataResult
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

    @Slot()
    def _select_axis_data(self):
        """
        Handles the selection of axis data from the combo boxes
        and emits a signal to request the data.

        This method retrieves the selected axis names from the combo boxes,
        looks up their corresponding paths in the `axis_options_path` 
        dictionary, and emits the `request_data_sig` signal with these paths 
        to request the data for plotting.
        
        Parameters
        ----------
        None
        
        Notes
        -----
        This method is called when the user selects an axis from either
        combo box, and it ensures that the correct data paths are sent to
        the main application for fetching and plotting the data.
        """

        x_axis = self.x_axis_combobox.currentText()
        y_axis = self.y_axis_combobox.currentText()
        
        x_path = self.axis_options_path[x_axis]
        y_path = self.axis_options_path[y_axis]

        self.request_data_sig.emit(x_path, y_path)

    @Slot()
    def _select_hdf5_file(self):
        """
        Opens a file dialog for the user to select an HDF5 file and emits a 
        signal with the selected file path.
        
        This method creates a QFileDialog, sets it to open in a default
        directory (checking possible paths), and filters for HDF5 files. 
        When the user selects a file, it emits the `import _hdf5_sig` signal
        with the absolute path of the selected file, allowing the main 
        application to handle loading the HDF5 data.
        
        Notes
        -----
        The method also handles the case where the user cancels the file 
        dialog, in which case it simply returns without emitting any signal.
        """

        dialog = QFileDialog(self)
        directory = os.path.expanduser("~")
        for path in self.possible_data_paths:
            if os.path.exists(path):
                 directory = path
                 break
        dialog.setDirectory(directory)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setNameFilter('HDF5 data files (*.h5)')
        dialog.setViewMode(QFileDialog.ViewMode.Detail)
        if dialog.exec():
            file_path = dialog.selectedFiles()[0]
            file_type = dialog.selectedNameFilter()
        else:
            return
        filepath = os.path.abspath(file_path)
        if filepath != "":
            self.import_hdf5_sig.emit(filepath)

    @Slot(dict)
    def update_imported_data_tree(self, structure: dict):
        """
        Updates the imported data tree with the provided HDF5 file structure.
        
        This method takes a dictionary representing the structure of the 
        imported HDF5 file (including groups and datasets) and populates the
        QTreeWidget with this information. It starts from the root and 
        recursively adds tree items for groups and datasets, storing the full 
        path and type information in the item data for later use when the user 
        interacts with the tree.
        
        Parameters
        ----------
        structure : dict
            A dictionary representing the structure of the imported HDF5 file, 
            where keys are paths and values contain information about the type 
            (Group or Dataset), shape (datasets), and children (groups).
        
        Notes
        -----
        This method clears any existing items in the tree before populating it
        with the new structure, and expands all tree items after adding them.
        """

        self.imported_data_tree.clear()
        self.x_axis_combobox.clear()
        self.y_axis_combobox.clear()
        self.axis_options_path = {}
        
        # We start from the root "/"
        root_item = QTreeWidgetItem(self.imported_data_tree, ["/"])
        root_item.setData(0, Qt.ItemDataRole.UserRole, {"path": "/", "type": "Group"})
        
        self._add_tree_nodes(structure["/"].get("children", {}), root_item)
        self.imported_data_tree.expandAll()

    def _add_tree_nodes(self, data, parent_item):
        """
        Recursively adds tree nodes to the QTreeWidget based 
        on the provided data structure.

        This method takes a dictionary representing the children of a group in 
        the HDF5 structure and a parent tree item, and it creates tree items 
        for each child, storing the path and type information in the item data.
        If a child is a group, it recursively calls itself to add its children. 
        If a child is a dataset with shape information, it also adds it to the 
        axis options for plotting.

        Parameters
        ----------
        data : dict
            A dictionary representing the children of a group in the HDF5 
            structure, where keys are names of the children and values contain 
            information about their type (Group or Dataset), shape 
            (for datasets), and their own children (for groups).
        parent_item : QTreeWidgetItem
            Parent tree item to which the new items will be added as children. 
            This is used to build the tree structure in the QTreeWidget.

        Notes
        -----
        This method is called recursively to build the entire tree structure 
        of the imported HDF5 file, starting from the root and adding groups 
        and datasets as tree items. It also populates the axis options for 
        datasets that have shape information, allowing them to be selected 
        for plotting in the main application.
        """
        for name, info in data.items():
            # Create the tree item with the name (e.g., 'Exp_001')
            item = QTreeWidgetItem(parent_item, [name])
            
            # Store the full HDF5 path (e.g., '/Data/Pulsed/Exp_001')
            # This is vital for the Dataclass request later
            current_path = f"{parent_item.data(0, Qt.ItemDataRole.UserRole)['path']}/{name}".replace("//", "/")
            item.setData(0, Qt.ItemDataRole.UserRole, {"path": current_path, "kind": info["type"], "shape": info.get("shape", False)})
            
            # If it's a group, recurse to add its children
            if info["type"] == "Group":
                self._add_tree_nodes(info.get("children", {}), item)
            if info["type"] == "Dataset" and info.get("shape", False):
                self._add_axis_options(name, info, current_path)

    def _add_axis_options(self, name: str, info: dict, path: str):
        """
        Adds dataset options to the axis selection combo boxes if they are 1D.

        This method checks if the provided dataset information corresponds to 
        a 1D dataset (i.e., it has a shape of length 1) and, if so, it adds 
        the dataset name to both the x-axis and y-axis combo boxes for 
        selection. It also stores the full path of the dataset in the 
        `axis_options_path` dictionary, allowing the main application to 
        retrieve the correct data when the user selects an axis.

        Parameters
        ----------
        name : str
            The name of the dataset, which will be displayed in the combo boxes.
        info : dict
            A dictionary containing information about the dataset, 
            including its shape and type.
        path : str
            The full HDF5 path to the dataset, which will be stored for later 
            retrieval when the user selects this dataset as an axis option.

        Notes
        -----
        This method is called for each dataset that has shape information when 
        building the tree structure, and it ensures that only 1D datasets are 
        added as options for the axes, as these are typically used for plotting
        against each other in a 2D plot.
        """

        if "Analysis" not in path.strip("/"):
            if len(info["shape"]) == 1:
                self.axis_options_path[name] = path
                self.x_axis_combobox.addItem(name)
                self.y_axis_combobox.addItem(name)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    explorer = HDF5ExplorerDock()
    explorer.show()
    sys.exit(app.exec())