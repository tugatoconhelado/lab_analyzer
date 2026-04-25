import numpy as np
import os
import sys
import datetime
from dataclasses import dataclass
from PyQt5.QtCore import QObject, pyqtSignal as Signal, pyqtSlot as Slot
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.core.structures import Dataset, WorkbenchAsset


class WorkbenchRegistry(QObject):

    registry_changed = Signal()

    def __init__(self, kernel_shell):
        super().__init__()
        self.shell = kernel_shell
        self._data_store = {}
        self._metadata = {}

    def add(self, name, obj: WorkbenchAsset, source="User") -> WorkbenchAsset:
        """Called by Engine or ModelManager."""
        obj_type = obj.kind 
        self._data_store[name] = obj
        self._metadata[name] = {
            "name": name,
            "type": obj_type,
            "source": source,
            "shape": str(getattr(obj, 'shape', 'N/A'))
        }
        if self.shell is not None:
            self.shell.user_ns[name] = obj
        self.registry_changed.emit()
        print(f"Added '{name}' of type '{obj_type}' to WorkbenchRegistry.")
        return obj

    def get(self, name):
        item = self._data_store.get(name, None)
        if item is None:
            raise KeyError(f"No item named '{name}' found in WorkbenchRegistry.")
        return item


if __name__ == '__main__':

    d1 = Dataset(
        name="test1"
    )
    d2 = Dataset(
        name="test2"
    )
    d3 = Dataset(
        name="test3"
    )
    print(d1)
    bench = WorkbenchRegistry(None)
    bench.add("test1", d1, "Dataset")
    bench.add("test2", d2, "Dataset")
    bench.add("test3", d3, "Dataset")
    print(bench.get("test2"))
    print(bench)