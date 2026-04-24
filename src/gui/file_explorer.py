import os
from PyQt5.QtWidgets import (QDockWidget, QTreeView, QVBoxLayout, 
                             QWidget, QLineEdit, QFileSystemModel)
from PyQt5.QtCore import Qt, QDir
from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtCore import pyqtSlot as Slot
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from resources.ui.ui_files_dock import Ui_files_dockwidget

class FileExplorerDock(QDockWidget, Ui_files_dockwidget):

    import_hdf5_sig = Signal(str)

    def __init__(self, title, root_path=None, parent=None):
        super().__init__(title, parent)
        self.setupUi(self)

        self.model = QFileSystemModel()
        
        # Set the root path to your lab data folder or home directory
        if root_path is None:
            root_path = QDir.currentPath()
        
        self.model.setRootPath(root_path)
        
        # Filter for specific lab data extensions
        self.model.setNameFilters(["*.hdf5", "*.h5", "*.dat", "*.csv"])
        self.model.setNameFilterDisables(False) # Hide files that don't match

        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(root_path))
        
        self.tree.setAnimated(True)
        self.tree.setIndentation(20)
        self.tree.setSortingEnabled(True)
        self.tree.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        
        # 5. Connect Signals
        self.search_bar.textChanged.connect(self.update_filter)
        self.tree.doubleClicked.connect(self.on_file_double_clicked)

    def connect_to_bridge(self, bridge):
        self.import_hdf5_sig.connect(bridge.import_hdf5_data)

    def update_filter(self, text):
        """
        Update the name filters based on search bar text.
        """
        if not text:
            self.model.setNameFilters(["*.hdf5", "*.h5", "*.dat", "*.csv"])
        else:
            # Allows user to type "rabi" to find "rabi_001.hdf5"
            self.model.setNameFilters([f"*{text}*"])

    def on_file_double_clicked(self, index):
        """
        Handle loading the file when the user double-clicks.
        """
        file_path = self.model.filePath(index)
        if os.path.isfile(file_path):
            print(f"Loading experiment data from: {file_path}")
            # Here you would call your Hub's load_data function
            self.import_hdf5_sig.emit(file_path)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    dock = FileExplorerDock("Experiment Data", root_path=os.path.expanduser("~/Scripts/data"))
    dock.show()
    sys.exit(app.exec())