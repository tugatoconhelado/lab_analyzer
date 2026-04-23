import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from PyQt5.QtWidgets import (QSplitter, QTreeView, QTreeWidget, QWidget, QVBoxLayout, QTabWidget, 
    QTableWidget, QHeaderView, QTableWidgetItem, QAbstractItemView)
from PyQt5.QtCore import Qt, pyqtSignal as Signal, pyqtSlot as Slot
from PyQt5.QtGui import QColor, QStandardItemModel, QStandardItem

from src.gui.console.console import ConsoleWidget
from src.gui.console.editor import EditorWidget
from src.gui.console.variable_explorer import VariableExplorer
from src.core.structures import WorkbenchAsset


class WorkspaceWidget(QWidget):
    """
    The central container for the Console and Explorer.
    """
    def __init__(self, parent=None, kernel_manager=None, kernel_client=None):
        super().__init__(parent)

        self.main_layout = QVBoxLayout(self)

        self.splitter = QSplitter(Qt.Orientation.Vertical)

        self.console = ConsoleWidget(self, kernel_manager, kernel_client)
        self.editor = EditorWidget(self)
        self.workbench = WorkbenchExplorer(self)
        
        if self.console.console.kernel_manager is not None:
            self.variable_explorer = VariableExplorer(
                self.console.console.kernel_manager.kernel.shell)
        
        # Expose the Hub itself to the console so the user can
        # script the UI (e.g., 'hub.spawn_plot()')
        self.console.refresh_variable_explorer_sig.connect(
            self.variable_explorer.refresh)

        self.tab_widget = QTabWidget(self)
        self.tab_widget.addTab(self.workbench, "Workbench")
        self.tab_widget.addTab(self.variable_explorer, "Variables")
        self.tab_widget.addTab(self.editor, "Editor")

        self.splitter.addWidget(self.tab_widget)
        self.splitter.addWidget(self.console)
        
        # Set a 60/40 initial split
        self.splitter.setSizes([600, 400])
        
        self.main_layout.addWidget(self.splitter)

        self.editor.run_code_signal.connect(self.execute_code)

    def execute_code(self, code):
        """Sends code to the kernel and ensures the console tracks it."""
        # This makes the code appear in the console as if you typed it there
        self.console.execute(code)
        
        # Pro-Tip: After running code, set focus back to editor 
        # so you can keep typing without clicking.
        self.editor.setFocus()

    def connect_to_bridge(self, bridge):
        bridge.refresh_registry_sig.connect(
            self.workbench.refresh
        )
        self.workbench.set_registry(bridge.registry)


class WorkbenchExplorer(QTreeView):

    def __init__(self, parent=None):
        super().__init__(parent)

        self._added_items = 0

        # 1. Create the Model
        self._model = QStandardItemModel()
        self._model.setHorizontalHeaderLabels(["Name", "Type", "Details"])
        self.setModel(self._model)
        
        # 2. Setup visual behavior
        header = self.header()
        if header is not None:
            header.setSectionResizeMode(0, QHeaderView.Stretch) # Column 0 adjusts to text
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  
            header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  
        width = 600
        self.setEditTriggers(QTreeView.NoEditTriggers) # Read-only
        self.setSelectionBehavior(QTreeView.SelectRows)

        # 3. Create top-level "folders" for organization
        self.root_nodes = {
            "Datasets": QStandardItem("Datasets"),
            "Fits": QStandardItem("Fits"),
            "Plots": QStandardItem("Plots"),
            "Traces": QStandardItem("Traces")
        }
        
        for node in self.root_nodes.values():
            node.setEditable(False)
            self._model.appendRow(node)
            
        self.expandAll() # Keep folders open by default

    def set_registry(self, registry):
        self.registry_ref = registry
        self.registry_ref.registry_changed.connect(
            self.refresh
        )

    def add_item(self, item: WorkbenchAsset):

        category = "Datasets"
        name = item.name
        kind = item.asset_type
        content = item.content

        # Decide category based on type or name heuristics
        if "fit" in kind.lower() or "model" in kind.lower():
            category = "Fits"
        elif "plot" in kind.lower():
            category = "Plots"

        if kind == "FitResult":
            self.add_fit_to_tree(content)
            return
        elif kind == "Trace":
            self.add_trace_to_tree(content)
            return
            
        # Create the row items
        if kind == "Dataset":
            name = "📊 " + name
        name_item = QStandardItem(name)
        type_item = QStandardItem(kind)
        
        # Extract shape or size if it exists (common for numpy/lab data)
        detail_str = str(getattr(content, 'shape', 'N/A'))
        detail_item = QStandardItem(detail_str)
        
        # Append as a child to the correct folder
        self.root_nodes[category].appendRow([name_item, type_item, detail_item])

    def remove_item(self, item: WorkbenchAsset):

        name = getattr(item, 'name', 'N/A')
        kind = getattr(item, 'asset_type', 'N/A')
        shape = getattr(item.content, 'shape', 'N/A')

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
        print("Refreshing Workbench Explorer...")  # Debug statement
        registry_data = self.registry_ref._data_store
        print(registry_data.keys())  # Debug: Show current registry contents
        """Redraws the table based on the current Registry state."""
        if not registry_data:
            return
        
        # Clear existing children of the folders, but keep the folders
        for node in self.root_nodes.values():
            node.removeRows(0, node.rowCount())

        for name, obj in registry_data.items():
            self.add_item(obj)

    def add_trace_to_tree(self, trace_obj):

        trace_node = QStandardItem(f"🔗 Trace: {trace_obj.name}")
        trace_node.setForeground(QColor("blue"))
        trace_node.setData(trace_obj, Qt.ItemDataRole.UserRole) # Store the Trace object
        
        x_row = self._construct_item_row(trace_obj.x_ds, name=f"🔗 X-Axis: {trace_obj.x_ds.name}")
        y_row = self._construct_item_row(trace_obj.y_ds, name=f"🔗 Y-Axis: {trace_obj.y_ds.name}")

        trace_node.appendRow(x_row)
        trace_node.appendRow(y_row)

        self.root_nodes["Traces"].appendRow(trace_node)


    def add_fit_to_tree(self, fit_obj):
        """Adds a FitResult as a expandable branch in the tree."""
        # 1. Create the Main Fit Row
        fit_node = QStandardItem(f"📉 Fit: {fit_obj.name}")
        fit_node.setForeground(QColor("red"))
        fit_node.setData(fit_obj, Qt.ItemDataRole.UserRole) # Store the FitResult object
        
        # We display the name of the source, but the icon/text shows it's a link
        trace_name = f"🔗 Trace: {fit_obj.trace.name}"
        curve_name = f"📈 {fit_obj.curve.name}"
        trace_row = self._construct_item_row(fit_obj.trace, name=trace_name)
        curve_row = self._construct_item_row(fit_obj.curve, name=curve_name)

        fit_node.appendRow(trace_row)
        fit_node.appendRow(curve_row)
        
        self.root_nodes["Fits"].appendRow(fit_node)

    def _construct_item_row(self, item, name: str = ""):

        item_name = getattr(item, 'name', 'N/A')
        if not name:
            name = item_name
        kind = type(item).__name__
        shape = str(getattr(item, 'shape', 'N/A'))

        name_item = QStandardItem(name)
        name_item.setData(item_name, Qt.ItemDataRole.UserRole + 1)
        type_item = QStandardItem(kind)
        shape_item = QStandardItem(shape)

        return [name_item, type_item, shape_item]

    def on_item_double_clicked(self, index):
        item = self._model.itemFromIndex(index)
        if item is None:
            return
        link_target = item.data(Qt.ItemDataRole.UserRole + 1) # Check for our secret link data
        
        if link_target:
            # 1. Look through the "Datasets" folder for the matching name
            for row in range(self.root_nodes["Datasets"].rowCount()):
                ds_item = self.root_nodes["Datasets"].child(row)
                if ds_item is not None and ds_item.text() == link_target:
                    # 2. Highlight the original data!
                    self.setCurrentIndex(ds_item.index())
                    print(f"Jumped to source data: {link_target}")
                    break

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    from qtconsole.inprocess import QtInProcessKernelManager
    import numpy as np

    app = QApplication(sys.argv)
    kernel_manager = QtInProcessKernelManager()
    kernel_manager.start_kernel()
    kernel_client = kernel_manager.client()
    kernel_client.start_channels()
    widget = WorkspaceWidget(None, kernel_manager, kernel_client)
    widget.workbench.add_item(WorkbenchAsset(
        name="Test item",
        content=np.array([1, 2, 3]),
        asset_type="Dataset"
    ))
    widget.workbench.add_item(WorkbenchAsset(
        name="Var2",
        content=None,
        asset_type="Group"
    ))
    widget.workbench.add_item(WorkbenchAsset(
        name="Var3",
        content=np.array([4, 5, 6]),
        asset_type="Dataset"
    ))
    # widget.workbench.remove_item(WorkbenchAsset(
    #     name="Var2",
    #     content=None,
    #     asset_type="Group"
    # ))
    widget.resize(800, 600)
    widget.show()
    sys.exit(app.exec())