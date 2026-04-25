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
from src.gui.console.workbench_explorer import WorkbenchExplorer


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
            self.workbench._model.refresh
        )
        self.workbench._model.set_registry(bridge.registry)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    from qtconsole.inprocess import QtInProcessKernelManager

    app = QApplication(sys.argv)
    kernel_manager = QtInProcessKernelManager()
    kernel_manager.start_kernel()
    kernel_client = kernel_manager.client()
    kernel_client.start_channels()
    widget = WorkspaceWidget(None, kernel_manager, kernel_client)
    widget.resize(800, 600)
    widget.show()
    sys.exit(app.exec())