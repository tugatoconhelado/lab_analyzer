import os
import sys

from PyQt5.QtWidgets import QAbstractButton, QDockWidget, QButtonGroup, QFileDialog, QHBoxLayout, QLabel, QTreeWidgetItem, QHeaderView, QMenu, QSplitter
from PyQt5.QtCore import QRectF, Qt, QPoint
from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtCore import pyqtSlot as Slot
from PyQt5.uic import loadUi
import pyqtgraph as pg
import numpy as np

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from src.core.structures import InspectInfo, DataResult
from src.gui.file_loader.file_previewer import FilePreviewer



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
    request_data_sig = Signal(str, str)
    import_hdf5_sig = Signal(str)
    load_to_workbench = Signal(str)
    current_item_path = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        loadUi(
            os.path.join('resources', 'ui', 'hdf5_explorer.ui'), self
        )
        self._setup_previewer()

        self.current_file = None
        self.possible_data_paths = [
            os.path.join(os.path.expanduser("~"), "Scripts", "data"),
            os.path.join("C:", "EXP", "data")
        ]
        self.axis_options_path = {}
        self.preview_index = 2

        self.imported_data_tree.currentItemChanged.connect(
            self._on_tree_selection_changed
        )
        self.load_button.clicked.connect(
            self._select_hdf5_file
        )

        self.imported_data_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        
        self.imported_data_tree.customContextMenuRequested.connect(self.show_context_menu)

    def _setup_previewer(self):

        self.previewer = FilePreviewer(self)
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.splitter.addWidget(self.imported_data_tree)
        self.splitter.addWidget(self.previewer)

        self.explorer_layout.addWidget(self.splitter)

        self.current_item_path.connect(
            self.previewer.update_preview_state
        )
        self.previewer.request_current_item_path.connect(
            self.handle_item_request
        )

    def handle_item_request(self):

        current = self.imported_data_tree.currentItem()
        if current is not None:
            self._on_tree_selection_changed(current, None)

    def connect_to_bridge(self, bridge):

        self.previewer.request_inspect_info_sig.connect(
            bridge.fetch_inspect_info
        )
        bridge.inspect_info_sig.connect(
            self.previewer.update_inspect_info
        )
        # Setting axis data
        self.request_data_sig.connect(
            bridge.fetch_data
        )
        self.previewer.request_preview_sig.connect(
            bridge.fetch_preview_data
        )
        bridge.preview_data_sig.connect(
            self.previewer.update_preview_plot
        )
        self.import_hdf5_sig.connect(
            bridge.import_hdf5_data
        )
        bridge.imported_data_sig.connect(
            self.update_imported_data_tree
        )


    def show_context_menu(self, position: QPoint):
        # 3. Find the item at the clicked position
        item = self.imported_data_tree.itemAt(position)
        
        # Only show the menu if the user actually clicked on an item
        if item:
            menu = QMenu()
            select_action = menu.addAction("Load to Workbench")
            
            # 4. Display the menu and capture the action
            action = menu.exec(self.imported_data_tree.viewport().mapToGlobal(position))
            
            # If "Select" was clicked, perform your logic
            if action == select_action:
                self.handle_selection(item)

    def handle_selection(self, item):
        path = item.data(0, Qt.ItemDataRole.UserRole)["path"]
        print(f"User selected: {path}")
        self.load_to_workbench.emit(path)

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
        self.previewer.update_preview_state(path, kind, shape)

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
        self.axis_options_path = {}
        
        # We start from the root "/"
        root_item = QTreeWidgetItem(self.imported_data_tree, ["/", 'Group'])
        root_item.setData(0, Qt.ItemDataRole.UserRole, {"path": "/", "type": "Group"})
        
        self._add_tree_nodes(structure["/"].get("children", {}), root_item)
        self.imported_data_tree.expandAll()
        self.imported_data_tree.resizeColumnToContents(0)

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
            item = QTreeWidgetItem(parent_item, [name, info['type']])
            
            # Store the full HDF5 path (e.g., '/Data/Pulsed/Exp_001')
            # This is vital for the Dataclass request later
            current_path = f"{parent_item.data(0, Qt.ItemDataRole.UserRole)['path']}/{name}".replace("//", "/")
            item.setData(0, Qt.ItemDataRole.UserRole, {"path": current_path, "kind": info["type"], "shape": info.get("shape", False)})
            
            # If it's a group, recurse to add its children
            if info["type"] == "Group":
                self._add_tree_nodes(info.get("children", {}), item)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    explorer = HDF5ExplorerDock()
    explorer.show()

    tree = {
        '/': {
            'type': 'Group',
            'children': {
                'Analysis': {
                    'type': 'Group',
                    'children': {
                        '20260416-1304-53_SingleExponential': {
                            'type': 'Group',
                            'children': {
                                'ModelTraces': {
                                    'type': 'Group',
                                    'children': {
                                        'fit_x': {'type': 'Dataset', 'shape': (30,)},
                                        'fit_y': {'type': 'Dataset', 'shape': (30,)},
                                        'residuals': {'type': 'Dataset', 'shape': (30,)},
                                        'x': {'type': 'Dataset', 'shape': (30,)},
                                        'y': {'type': 'Dataset', 'shape': (30,)}
                                    }
                                },
                                'parameters': {'type': 'Dataset'},
                                'report': {'type': 'Dataset'}
                            }
                        }
                    }
                },
                'Data': {
                    'type': 'Group',
                    'children': {
                        'pl_mean': {'type': 'Dataset', 'shape': (30,)},
                        'pl_raw_mean': {'type': 'Dataset', 'shape': (10, 30, 2)},
                        'pl_raw_std': {'type': 'Dataset', 'shape': (10, 30, 2)},
                        'pl_std': {'type': 'Dataset', 'shape': (30,)},
                        'tau': {'type': 'Dataset', 'shape': (30,)}
                    }
                }
            }
        }
    }
    explorer.update_imported_data_tree(tree)
    sys.exit(app.exec())