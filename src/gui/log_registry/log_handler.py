import logging
from PyQt5.QtCore import QAbstractTableModel, QObject, QPersistentModelIndex, Qt, QModelIndex
from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtCore import pyqtSlot as Slot
from PyQt5.QtGui import QColor, QBrush


class QtLogHandler(logging.Handler, QObject):
    # This signal carries the formatted log string
    new_record = Signal(dict)

    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)
        
    def emit(self, record: logging.LogRecord) -> None: # type: ignore[override]
        formatter = self.formatter or logging.Formatter()
        log_entry = {
            "time": formatter.formatTime(record, formatter.datefmt),
            "level": record.levelname,
            "name": record.name,
            "msg": record.getMessage(),
        }
        self.new_record.emit(log_entry)


class LogModel(QAbstractTableModel):


    def __init__(self, parent=None):
        super().__init__(parent)
        self._logs = [] # List of dicts: {"time":..., "level":..., "name":..., "msg":...}
        self.columns = ["Time", "Level", "Origin", "Message"]

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._logs)

    def columnCount(self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.columns)

    def data(self, index, role=int(Qt.ItemDataRole.DisplayRole)):
        if not index.isValid():
            return None
        
        log = self._logs[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return log['time']
            if col == 1: return log['level']
            if col == 2: return log['name']
            if col == 3: return log['msg']

        # The "High-End" Touch: Color-coding rows by severity
        if role == Qt.ItemDataRole.ForegroundRole:
            if log['level'] == "ERROR":
                return QBrush(QColor("#ff5555")) # Red
            if log['level'] == "WARNING":
                return QBrush(QColor("#ffb86c")) # Orange
        
        return None

    def headerData(self, section, orientation, role=int(Qt.ItemDataRole.DisplayRole)):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.columns[section]
        return None

    def add_log(self, log_entry: dict):
        """Adds a new log and notifies the view to update."""
        self.beginInsertRows(QModelIndex(), len(self._logs), len(self._logs))
        self._logs.append(log_entry)
        self.endInsertRows()
        #self.layoutChanged.emit()