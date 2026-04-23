import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from PyQt5.QtWidgets import (QSplitter, QWidget, QVBoxLayout, QTabWidget, 
    QTableWidget, QHeaderView, QTableWidgetItem, QAbstractItemView)
from PyQt5.QtCore import Qt, pyqtSignal as Signal, pyqtSlot as Slot

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
        
        self.variable_explorer = VariableExplorer(self.console.console.kernel_manager.kernel.shell)
        
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
        self._bridge = bridge
        self._bridge.registry.registry_changed.connect(
            self.workbench.refresh
        )



class WorkbenchExplorer(QTableWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self._added_items = 0

        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["Name", "Type", "Value/Shape"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

    def set_registry(self, registry):
        self.registry = registry

    def add_item(self, item: WorkbenchAsset):

        row = self._added_items
        self._added_items += 1
        self.setRowCount(self._added_items)

        name = getattr(item, 'name', 'N/A')
        kind = getattr(item, 'asset_type', 'N/A')
        shape = getattr(item.content, 'shape', 'N/A')

        name_item = QTableWidgetItem(str(name))
        kind_item = QTableWidgetItem(str(kind))
        shape_item = QTableWidgetItem(str(shape))

        self.setItem(row, 0, name_item)
        self.setItem(row, 1, kind_item)
        self.setItem(row, 2, shape_item)

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
        """Redraws the table based on the current Registry state."""
        if not self.registry:
            return

        # Clear the table
        self.setRowCount(0)
        
        # Loop through everything in the registry and add a row for each
        for name, obj in self.registry._data_store.items():
            self.add_item(obj)
                        

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
        data=np.array([1, 2, 3]),
        asset_type="Dataset"
    ))
    widget.workbench.add_item(WorkbenchAsset(
        name="Var2",
        data=None,
        asset_type="Group"
    ))
    widget.workbench.add_item(WorkbenchAsset(
        name="Var3",
        data=np.array([4, 5, 6]),
        asset_type="Dataset"
    ))
    widget.workbench.remove_item(WorkbenchAsset(
        name="Var2",
        data=None,
        asset_type="Group"
    ))
    widget.resize(800, 600)
    widget.show()
    sys.exit(app.exec())