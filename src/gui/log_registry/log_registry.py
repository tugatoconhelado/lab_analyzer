import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))


from PyQt5.QtWidgets import QAbstractItemView, QDockWidget, QHeaderView
from PyQt5.QtCore import Qt, pyqtSignal as Signal
from PyQt5.QtCore import pyqtSlot as Slot

from resources.ui.ui_log_registry import Ui_LogRegistryDock
from src.gui.log_registry.log_handler import QtLogHandler, LogModel, LevelFilter
import logging


class LogRegistryDock(QDockWidget, Ui_LogRegistryDock):
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

    def __init__(self, parent=None, level_filter=None):
        super().__init__(parent)
        self.setupUi(self)

        self.log_model = LogModel()
        self.log_view.setModel(self.log_model)
        self.level_filter = level_filter or LevelFilter()

        header = self.log_view.horizontalHeader()

        # Message column expands
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch) 
        self.log_view.setColumnWidth(0, 150)
        self.log_view.setColumnWidth(2, 150)
        # Hide row numbers
        self.log_view.verticalHeader().setVisible(False)
        self.log_view.setAlternatingRowColors(True)
        self.log_view.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        
        self.filter_tree.itemChanged.connect(self.handle_check_change)
        
    def connect_handler(self, handler: QtLogHandler | None):
        """
        Connects an external QtLogHandler to this dock's log model.
        
        Parameters
        ----------
        handler : QtLogHandler
            The logging handler whose new_record signal will be connected to the 
            log_model's add_log slot.
        """
        if handler is None:
            self.handler = QtLogHandler()
        else:   
            self.handler = handler
        date_format = '%Y-%m-%d %H:%M:%S'
        formatter = logging.Formatter('%(asctime)s', datefmt=date_format)
        self.handler.setFormatter(formatter)
        self.handler.new_record.connect(self.log_model.add_log)
        self.handler.new_record.connect(lambda _: self.log_view.scrollToBottom())


    def handle_check_change(self, item, column):

        self.filter_tree.blockSignals(True)
        # If "All" is clicked, set all children to match
        if item == self.filter_tree.topLevelItem(0):
            state = item.checkState(0)
            for i in range(item.childCount()):
                item.child(i).setCheckState(0, state)
        
        # "All" state based on children
        else:
            self.update_parent_state()

        self.filter_tree.blockSignals(False)
        self.sync_filter_to_tree()
        self.apply_filter_to_table()

    def sync_filter_to_tree(self):
        new_whitelist = set()
        root = self.filter_tree.topLevelItem(0)
        if root is None:
            return
        for i in range(root.childCount()):
            child = root.child(i)
            if child.checkState(0) == Qt.Checked:
                new_whitelist.add(child.text(0).upper())
        self.level_filter.enabled_levels = new_whitelist
        logging.info(f"UI Filter updated: {new_whitelist}")

    def apply_filter_to_table(self):
        # Get the currently enabled levels from your filter
        enabled = self.level_filter.enabled_levels
        
        # Block signals to prevent flickering during mass updates
        self.log_view.setUpdatesEnabled(False)
        
        for row in range(self.log_model.rowCount()):
            level_item = self.log_model.data(self.log_model.index(row, 1), Qt.ItemDataRole.DisplayRole)
            if isinstance(level_item, str):
                level_text = level_item.upper()
                # Hide the row if it's not in the whitelist
                self.log_view.setRowHidden(row, level_text not in enabled)
                
        self.log_view.setUpdatesEnabled(True)

    def update_parent_state(self):
        root = self.filter_tree.topLevelItem(0)
        if root is None:
            return
        checked_count = 0
        child_count = root.childCount()

        for i in range(child_count):
            if root.child(i).checkState(0) == Qt.Checked:
                checked_count += 1

        if checked_count == 0:
            root.setCheckState(0, Qt.Unchecked)
        elif checked_count == child_count:
            root.setCheckState(0, Qt.Checked)
        else:
            # This shows the "square" fill in the checkbox
            root.setCheckState(0, Qt.PartiallyChecked)



if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = LogRegistryDock()
    window.connect_handler(None)  # Connect a new handler for testing
    window.handler.addFilter(window.level_filter)
    window.show()

    # Set the global level to the lowest you want to see
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Show all logs DEBUG and above
    logger.addHandler(window.handler)  # Add the handler to the global logger

    # Example of logging from outside the widget
    logger.info("This is a test log message from outside the widget.")

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
    for i in range(2):
        logging.info(f"Simulated log message {i+1}")
        logging.debug(f"Simulated debug message {i+1}")
        logging.warning(f"Simulated warning message {i+1}")
        logging.error(f"Simulated error message {i+1}")
        logging.critical(f"Simulated critical message {i+1}")

    sys.exit(app.exec())