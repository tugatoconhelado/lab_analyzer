import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))


from PyQt5.QtWidgets import QAbstractItemView, QDockWidget, QHeaderView
from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtCore import pyqtSlot as Slot
from PyQt5.uic import loadUi
from src.gui.log_registry.log_handler import QtLogHandler, LogModel
import logging


class LogRegistryDock(QDockWidget):
    """
    Dock widget for displaying log messages in a structured format.
    
    Attributes
    ----------
    log_view : QTableView
        A table view that displays log entries with columns for time, level, 
        origin, and message.
    log_model : LogModel
        A custom table model that holds log entries and provides data to the 
        log_view.
    handler : QtLogHandler
        A custom logging handler that emits signals when new log records are 
        created, allowing the log_model to update in real-time.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        loadUi(
            os.path.join('resources', 'ui', 'log_registry.ui'), self
        )

        self.log_model = LogModel()
        self.log_view.setModel(self.log_model)

        header = self.log_view.horizontalHeader()

        # Message column expands
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch) 
        # Hide row numbers
        self.log_view.verticalHeader().setVisible(False)
        self.log_view.setAlternatingRowColors(True)
        self.log_view.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)

        self.handler = QtLogHandler()
        self.handler.setFormatter(logging.Formatter(datefmt='%H:%M:%S'))
        self.handler.new_record.connect(self.log_model.add_log)
        
        self.handler.new_record.connect(lambda _: self.log_view.scrollToBottom())

        logging.getLogger().addHandler(self.handler)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = LogRegistryDock()
    window.show()

    # Set the global level to the lowest you want to see
    logging.getLogger().setLevel(logging.DEBUG) 

    # Example of logging from outside the widget
    logging.info("This is a test log message from outside the widget.")

    # Simulate adding a log entry directly
    window.log_model.add_log({
        "time": "12:00:00",
        "level": "INFO",
        "name": "TestLogger",
        "msg": "This is a direct log entry added to the display."
    })

    # Simulate receiving a new log record (e.g., from the QtLogHandler)
    window.handler.new_record.emit({
        "time": "12:00:01",
        "level": "INFO",
        "name": "TestLogger",
        "msg": "Simulated log record received via signal."
    })

    # Simulate updating the log display with a new message
    for i in range(5):
        logging.info(f"Simulated log message {i+1}")
        logging.debug(f"Simulated debug message {i+1}")

    sys.exit(app.exec())