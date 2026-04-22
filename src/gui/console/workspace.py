import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from PyQt5.QtWidgets import (QSplitter, QWidget, QVBoxLayout, QTabWidget, 
    QTableWidget, QHeaderView, QTableWidgetItem, QAbstractItemView)
from PyQt5.QtCore import Qt

from src.gui.console.console import ConsoleWidget
from src.gui.console.editor import EditorWidget
from src.gui.console.variable_explorer import VariableExplorer


class WorkspaceWidget(QWidget):
    """
    The central container for the Console and Explorer.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        self.main_layout = QVBoxLayout(self)

        self.splitter = QSplitter(Qt.Orientation.Vertical)

        self.console = ConsoleWidget(self)
        self.editor = EditorWidget(self)
        self.workbench = WorkbenchExplorer(self)
        

        self.variable_explorer = VariableExplorer(self.console.kernel.shell)
        
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



class WorkbenchExplorer(QTableWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self._added_items = 0

        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["Name", "Type", "Value/Shape"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

    def add_item(self, item: dict):

        row = self._added_items
        self._added_items += 1
        self.setRowCount(self._added_items)

        name = item.get("name")
        kind = item.get("kind")
        shape = item.get("shape")

        name_item = QTableWidgetItem(str(name))
        kind_item = QTableWidgetItem(str(kind))
        shape_item = QTableWidgetItem(str(shape))

        self.setItem(row, 0, name_item)
        self.setItem(row, 1, kind_item)
        self.setItem(row, 2, shape_item)

    def remove_item(self, item: dict):

        name = str(item.get("name"))
        kind = str(item.get("kind"))
        shape = str(item.get("shape"))

        for row in range(self.rowCount()):
            item_name = self.item(row, 0).text()
            item_kind = self.item(row, 1).text()
            item_shape = self.item(row, 2).text()
            print(item_name, item_kind, item_shape)
            if item_name == name and item_kind == kind:
                if item_shape == shape:
                    self.removeRow(row)
                    return row
                    




if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    widget = WorkspaceWidget()
    widget.workbench.add_item({
        "name": "Test item",
        "kind": "Dataset",
        "shape": (100,)
    })
    widget.workbench.add_item({
        "name": "Var2",
        "kind": "Group",
        "shape": None
    })
    widget.workbench.add_item({
        "name": "Var3",
        "kind": "Dataset",
        "shape": (150,)
    })
    widget.workbench.remove_item({
        "name": "Var2",
        "kind": "Group",
        "shape": None
    })
    widget.resize(800, 600)
    widget.show()
    sys.exit(app.exec())