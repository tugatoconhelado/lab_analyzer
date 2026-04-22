import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from PyQt5.QtWidgets import QSplitter, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt

from src.gui.console.console import ConsoleWidget
from src.gui.console.editor import EditorWidget


class WorkbenchWidget(QWidget):
    """
    The central container for the Console and Explorer.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        self.main_layout = QVBoxLayout(self)

        self.splitter = QSplitter(Qt.Orientation.Vertical)

        self.console = ConsoleWidget(self)
        self.editor = EditorWidget(self)

        self.splitter.addWidget(self.editor)
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


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    widget = WorkbenchWidget()
    widget.resize(800, 600)
    widget.show()
    sys.exit(app.exec())