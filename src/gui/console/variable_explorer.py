import sys
from PyQt5.QtWidgets import (QDockWidget, QWidget, QVBoxLayout, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QSplitter,
                             QAbstractItemView)
from PyQt5.QtCore import Qt, QTimer

# Jupyter / QtConsole imports
from qtconsole.rich_jupyter_widget import RichJupyterWidget
from qtconsole.inprocess import QtInProcessKernelManager
from typing import cast


class VariableExplorer(QTableWidget):
    """
    A live table that inspects the Python namespace.

    This widget connects to the Jupyter kernel's shell and periodically
    refreshes to show the current variables, their types, and values/shapes.
    It filters out internal variables and provides a simple interface for 
    users to see what's in their console namespace.

    Attributes
    ----------
    shell : InteractiveShell
        The IPython shell instance from the Jupyter kernel, used to access the user namespace.
    timer : QTimer
        A timer that triggers periodic refreshes of the variable list.
    
    Methods
    -------
    refresh()
        Fetches the current variables from the kernel's namespace and updates the table display.
    """

    def __init__(self, kernel_shell, parent=None):
        super().__init__(parent)
        self.shell = kernel_shell
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["Name", "Type", "Value/Shape"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # Refresh timer (updates every 2 seconds to save CPU)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000)

    def refresh(self):
        """
        Fetch the current variables from the kernel's
        user namespace and update the table.
        
        This method is called periodically by the timer.
        It retrieves the variables, filters out internal ones,
        and populates the table with their names, types, and values/shapes.
        """
        # Filter out internal Python/Jupyter variables
        skip_list = ['In', 'Out', 'exit', 'quit', 'get_ipython']
        variables = {k: v for k, v in self.shell.user_ns.items() 
                    if not k.startswith('_') and k not in skip_list}

        self.setRowCount(len(variables))
        for i, (name, val) in enumerate(variables.items()):
            self.setItem(i, 0, QTableWidgetItem(str(name)))
            self.setItem(i, 1, QTableWidgetItem(type(val).__name__))
            if hasattr(val, 'shape'): # For NumPy arrays
                val_str = f"Array {val.shape}"
            else:
                val_str = str(val)[:50] # Truncate long strings
            
            self.setItem(i, 2, QTableWidgetItem(val_str))


class VariableExplorerDock(QDockWidget):
    """
    A dockable widget that contains the VariableExplorer.

    This class wraps the VariableExplorer in a QDockWidget, allowing it to be 
    docked within the main application window. It takes a reference to the 
    Jupyter kernel's shell to pass to the VariableExplorer.

    Attributes
    ----------
    explorer : VariableExplorer
        The instance of VariableExplorer contained within this dock widget.
    
    Methods
    -------
    __init__(kernel_shell, parent=None)
        Initializes the dock widget and creates the VariableExplorer with the provided kernel shell.
    """

    def __init__(self, kernel_shell, parent=None):
        super().__init__(parent)
        self.explorer = VariableExplorer(kernel_shell)
        self.setWidget(self.explorer)
        self.setWindowTitle("Variable Explorer")


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)

    # Setup a simple in-process kernel for testing
    kernel_manager = QtInProcessKernelManager()
    kernel_manager.start_kernel()
    kernel = kernel_manager.kernel
    kernel_client = kernel_manager.client()
    kernel_client.start_channels()

    window = VariableExplorerDock(kernel.shell)
    window.show()
    sys.exit(app.exec())