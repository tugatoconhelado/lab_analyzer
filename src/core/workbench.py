import numpy as np
import os
import sys
import datetime
from dataclasses import dataclass
from PyQt5.QtCore import QObject, pyqtSignal as Signal, pyqtSlot as Slot
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.core.structures import Dataset, WorkbenchAsset
import logging
logger = logging.getLogger(__name__)


class WorkbenchRegistry(QObject):

    registry_changed = Signal()

    def __init__(self, kernel_shell):
        super().__init__()
        self.shell = kernel_shell
        self._data_store = {}
        self._metadata = {}
        self._id_generator = 130910

    def add(self, name, obj: WorkbenchAsset, source="User") -> WorkbenchAsset:
        """Called by Engine or ModelManager."""

        if name in self._data_store:
            logger.warning(f"Overwriting existing asset '{name}' in WorkbenchRegistry.")

        obj.asset_id = self._id_generator
        self._id_generator += 1
        obj_type = obj.kind 

        self._data_store[obj.asset_id] = obj
        self._metadata[obj.asset_id] = {
            "name": name,
            "id": obj.asset_id,
            "type": obj_type,
            "source": source,
            "shape": str(getattr(obj, 'shape', 'N/A'))
        }

        if self.shell is not None:
            self.shell.user_ns[name] = obj

        self.registry_changed.emit()
        logger.info(f"Added '{name}' of type '{obj_type}' to WorkbenchRegistry.")
        return obj

    def get(self, asset_id):
        item = self._data_store.get(asset_id, None)
        if item is None:
            raise KeyError(f"No item with ID '{asset_id}' found in WorkbenchRegistry.")
        return item

    def get_from_name(self, name):
        for asset in self._data_store.values():
            if asset.name == name:
                return asset
        raise KeyError(f"No item with name '{name}' found in WorkbenchRegistry.")

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
    bench = WorkbenchRegistry(None)
    bench.add("test1", d1, "Dataset")
    bench.add("test2", d2, "Dataset")
    bench.add("test3", d3, "Dataset")