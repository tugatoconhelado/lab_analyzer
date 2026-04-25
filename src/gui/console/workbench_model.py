import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from PyQt5.QtWidgets import (QAction, QMenu, QSplitter, QTreeView, QTreeWidget, QWidget, QVBoxLayout, QTabWidget, 
    QTableWidget, QHeaderView, QTableWidgetItem, QAbstractItemView)
from PyQt5.QtCore import Qt, pyqtSignal as Signal, pyqtSlot as Slot
from PyQt5.QtGui import QColor, QStandardItemModel, QStandardItem

from src.gui.console.console import ConsoleWidget
from src.gui.console.editor import EditorWidget
from src.gui.console.variable_explorer import VariableExplorer
from src.core.structures import WorkbenchAsset
from src.core.constants import AssetType
import logging
logger = logging.getLogger(__name__)


class WorkbenchModel(QStandardItemModel):
    """
    The model for the Workbench Explorer tree view.

    This model organizes WorkbenchAssets into a hierarchical structure based on their type (Dataset, Fit, Plot, Trace).
    It provides methods for adding, removing, and updating assets in the model, as well as retrieving asset information
    based on tree indices.

    Attributes
    ----------
    registry : WorkbenchRegistry
        The registry that holds all WorkbenchAssets and provides access to them.

    Methods
    -------
    refresh()
        Refreshes the entire model by clearing it and re-adding all assets from the registry.
    add_asset(asset: WorkbenchAsset)
        Adds a single WorkbenchAsset to the appropriate category in the model.
    remove_asset(asset_id: str)
        Removes an asset from the model based on its unique ID.
    update_asset(asset: WorkbenchAsset)
        Updates an existing asset in the model with new information.
    get_asset_by_index(index: QModelIndex) -> WorkbenchAsset | None
        Retrieves the WorkbenchAsset associated with a given tree index, or returns None if the index
        does not correspond to a valid asset.
    """
    
    def __init__(self, registry):
        super().__init__()
        self.registry = registry
        self.setHorizontalHeaderLabels(["Name", "Type", "Details"])

        self.root_nodes = {
            "Datasets": QStandardItem("Datasets"),
            "Fits": QStandardItem("Fits"),
            "Plots": QStandardItem("Plots"),
            "Traces": QStandardItem("Traces")
        }

        for node in self.root_nodes.values():
            node.setEditable(False)
            self.appendRow(node)

    def set_registry(self, registry):
        self.registry_ref = registry
        self.registry_ref.registry_changed.connect(
            self.refresh
        )

    def add_item(self, item: WorkbenchAsset):

        category = "Datasets"
        name = item.name
        kind = item.kind

        if kind & AssetType.FIT or kind & AssetType.MODEL:
            category = "Fits"
            self._add_fit_to_tree(item)
            return
        elif kind & AssetType.TRACE:
            self._add_trace_to_tree(item)
            return
        elif kind & AssetType.DATASET:
            category = "Datasets"
            self._add_dataset_to_tree(item)
            return
        elif kind & AssetType.PLOT:
            category = "Plots"
            self._add_plot_to_tree(item)
            return
            
        # Create the row items
        if kind & AssetType.DATASET:
            name = "📊 " + name
        name_item = QStandardItem(name)
        type_item = QStandardItem(kind)
        
        # Extract shape or size if it exists (common for numpy/lab data)
        detail_str = str(getattr(item, 'shape', 'N/A'))
        detail_item = QStandardItem(detail_str)
        
        # Append as a child to the correct folder
        self.root_nodes[category].appendRow([name_item, type_item, detail_item])

    def remove_item(self, item: WorkbenchAsset):

        name = getattr(item, 'name', 'N/A')
        kind = getattr(item, 'kind', 'N/A')
        shape = getattr(item, 'shape', 'N/A')

        for row in range(self.rowCount()):
            name_cell = self.item(row, 0)
            kind_cell = self.item(row, 1)
            shape_cell = self.item(row, 2)

            # Skip incomplete/empty rows safely
            if name_cell is None or kind_cell is None or shape_cell is None:
                continue

            item_name = name_cell.text()
            item_kind = kind_cell.text()
            item_shape = shape_cell.text()
            print(item_name, item_kind, item_shape)
            if item_name == name and item_kind == kind:
                if item_shape == shape:
                    self.removeRow(row)
                    return row

    @Slot()
    def refresh(self):
        """Redraws the table based on the current Registry state."""
        logger.debug("Refreshing Workbench Explorer...")
        registry_data = self.registry_ref._data_store
        logger.debug(f"Current registry contents: {registry_data.keys()}")
    
        if not registry_data:
            return
        
        # Clear existing children of the folders, but keep the folders
        for node in self.root_nodes.values():
            node.removeRows(0, node.rowCount())

        for name, obj in registry_data.items():
            self.add_item(obj)

    def _add_dataset_to_tree(self, dataset_obj):

        dataset_node = QStandardItem(f"📊 {dataset_obj.name}")
        dataset_node.setForeground(QColor("green"))
        dataset_node.setData(dataset_obj, Qt.ItemDataRole.UserRole)
        dataset_node.setData(AssetType.DATASET, Qt.ItemDataRole.UserRole + 1)
        obj_name = getattr(dataset_obj, 'name', 'N/A')
        dataset_node.setData(obj_name, Qt.ItemDataRole.UserRole + 3)

        kind = type(dataset_obj).__name__
        shape = str(getattr(dataset_obj, 'shape', 'N/A'))

        type_item = QStandardItem(kind)
        shape_item = QStandardItem(shape)

        row = [dataset_node, type_item, shape_item]
        self.root_nodes["Datasets"].appendRow(row)

    def _add_trace_to_tree(self, trace_obj):

        trace_node = QStandardItem(f"🔗 Trace: {trace_obj.name}")
        trace_node.setForeground(QColor("blue"))
        trace_node.setData(trace_obj, Qt.ItemDataRole.UserRole)
        trace_node.setData(AssetType.TRACE, Qt.ItemDataRole.UserRole + 1)
        
        x_row = self._construct_item_row(
            trace_obj.x_ds, 
            name=f"🔗 X-Axis: {trace_obj.x_ds.name}",
            kind_id=AssetType.DATASET | AssetType.LINK,
            link=trace_obj.x_ds.name  
        )
        y_row = self._construct_item_row(
            trace_obj.y_ds,
            name=f"🔗 Y-Axis: {trace_obj.y_ds.name}",
            kind_id=AssetType.DATASET | AssetType.LINK,
            link=trace_obj.y_ds.name 
        )

        trace_node.appendRow(x_row)
        trace_node.appendRow(y_row)

        kind_item = QStandardItem("Trace")
        trace_node.setData(AssetType.TRACE, Qt.ItemDataRole.UserRole + 1)
        self.root_nodes["Traces"].appendRow([trace_node, kind_item, QStandardItem("")])

    def _add_fit_to_tree(self, fit_obj):
        """Adds a FitResult as a expandable branch in the tree."""
        # 1. Create the Main Fit Row
        fit_node = QStandardItem(f"📉 Fit: {fit_obj.name}")
        fit_node.setForeground(QColor("red"))
        fit_node.setData(fit_obj, Qt.ItemDataRole.UserRole)
        fit_node.setData(AssetType.FIT, Qt.ItemDataRole.UserRole + 1)

        trace_row = self._construct_item_row(
            fit_obj.trace,
            name=f"🔗 Trace: {fit_obj.trace.name}",
            kind_id=AssetType.TRACE | AssetType.LINK,
            link=fit_obj.trace.name
        )
        curve_row = self._construct_item_row(
            fit_obj.curve,
            name=f"📈 {fit_obj.curve.name}",
            kind_id=AssetType.DATASET | AssetType.LINK,
            link=fit_obj.curve.name
        )

        fit_node.appendRow(trace_row)
        fit_node.appendRow(curve_row)
        
        self.root_nodes["Fits"].appendRow(fit_node)

    def _add_plot_to_tree(self, plot_obj):
        plot_node = QStandardItem(f"🖼️ Plot: {plot_obj.name}")
        plot_node.setForeground(QColor("purple"))
        plot_node.setData(plot_obj, Qt.ItemDataRole.UserRole)
        plot_node.setData(AssetType.PLOT, Qt.ItemDataRole.UserRole + 1)

        kind_item = QStandardItem("Plot")
        self.root_nodes["Plots"].appendRow([plot_node, kind_item, QStandardItem("")])

    def _construct_item_row(self, item, name: str = "", kind_id: int = 0, link: str = ""):

        item_name = getattr(item, 'name', 'N/A')
        if not name:
            name = item_name
        kind = type(item).__name__
        shape = str(getattr(item, 'shape', 'N/A'))

        name_item = QStandardItem(name)
        name_item.setData(item, Qt.ItemDataRole.UserRole)
        name_item.setData(item_name, Qt.ItemDataRole.UserRole + 3)
        if link:
            # Store the link target in UserRole + 2 for later retrieval
            name_item.setData(link, Qt.ItemDataRole.UserRole + 2)
        if kind_id != 0:
            name_item.setData(kind_id, Qt.ItemDataRole.UserRole + 1)
        type_item = QStandardItem(kind)
        shape_item = QStandardItem(shape)

        return [name_item, type_item, shape_item]
    
    def find_linked_item_idx(self, link_target):
        
        for row in range(self.root_nodes["Datasets"].rowCount()):
            ds_item = self.root_nodes["Datasets"].child(row)
            item_name = ds_item.data(Qt.ItemDataRole.UserRole + 3)
            if ds_item is not None and item_name == link_target:
                return ds_item.index()