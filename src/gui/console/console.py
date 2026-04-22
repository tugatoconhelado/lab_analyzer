import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QSplitter,
                             QAbstractItemView)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtCore import pyqtSlot as Slot

# Jupyter / QtConsole imports
from qtconsole.rich_jupyter_widget import RichJupyterWidget
from qtconsole.inprocess import QtInProcessKernelManager
from typing import cast


class ConsoleWidget(QWidget):
    """
    The central container for the Console and Explorer.

    This widget uses a QSplitter to allow the user to resize the Console and Variable Explorer.
    It sets up an in-process Jupyter kernel and connects the console and explorer to it.

    Attributes
    ----------
    splitter : QSplitter
         The splitter that divides the console and explorer.
    kernel_manager : QtInProcessKernel
            The manager for the in-process Jupyter kernel.
     kernel : Kernel
        The Jupyter kernel instance.
     kernel_client : KernelClient
        The client for communicating with the Jupyter kernel.
     console : RichJupyterWidget
        The Jupyter console widget for executing code and displaying output.
     explorer : VariableExplorer
        The variable explorer widget that shows the current variables in the kernel's namespace.

     Methods
     -------
     push_to_console(variables: dict)
        Injects a dictionary of variables into the console's namespace, allowing them to be accessed in
        the console.
    """

    refresh_variable_explorer_sig = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)


        self.kernel_manager = QtInProcessKernelManager()
        self.kernel_manager.start_kernel()
        self.kernel = self.kernel_manager.kernel
        
        self.kernel_client = self.kernel_manager.client()
        self.kernel_client.start_channels()

        self.console = RichJupyterWidget()
        self.console.kernel_manager = self.kernel_manager
        self.console.kernel_client = self.kernel_client

        self.console.execute("%matplotlib inline")

        self.kernel_client.iopub_channel.message_received.connect(self.handle_iopub_message)

        layout.addWidget(cast(QWidget, self.console))

    def push_to_console(self, variables: dict):
        """Inject objects from the GUI into the console namespace."""
        self.kernel.shell.push(variables)

    def execute(self, code: str):
        """Execute code in the console's kernel."""
        self.console.execute(code)

    def handle_iopub_message(self, msg):
        """
        Sniffs all messages coming from the kernel.
        The 'status' message tells us if the kernel is busy or idle.
        """
        msg_type = msg.get('header', {}).get('msg_type')
        
        if msg_type == 'status':
            state = msg.get('content', {}).get('execution_state')
            
            if state == 'idle':
                # The kernel has finished the task (or crashed/errored)
                self.refresh_variable_explorer_sig.emit()
            elif state == 'busy':
                pass


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    widget = ConsoleWidget()
    widget.resize(800, 600)
    widget.show()
    sys.exit(app.exec())