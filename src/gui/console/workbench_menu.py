from dataclasses import dataclass
from typing import Callable

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAction, QMenu, QWidget

from src.core.constants import AssetType


@dataclass(frozen=True)
class WorkbenchMenuActions:
    create_new_trace: Callable[[], None]
    add_to_trace: Callable[[], None]
    create_plot: Callable[[], None]
    add_to_plot: Callable[[], None]
    export_hdf5: Callable[[], None]
    export_csv: Callable[[], None]
    delete_item: Callable[[], None]


class WorkbenchMenuHelper:
    def __init__(self, parent: QWidget, actions: WorkbenchMenuActions):
        self._parent = parent
        self._actions = actions
        self._context_menu = QMenu(parent)

        self._add_dataset_action = QAction("➕ Create Trace from Dataset", parent)
        self._add_dataset_action.triggered.connect(self._actions.create_new_trace)

        self._add_data_menu = QMenu("➕ Add to Trace", parent)
        self._add_to_trace_action = QAction("➕ Add to Trace", parent)
        self._add_to_trace_action.triggered.connect(self._actions.add_to_trace)
        self._add_data_menu.addAction(self._add_to_trace_action)

        self._add_to_plot_action = QAction("➕ Add to Active Plot", parent)
        self._add_to_plot_action.triggered.connect(self._actions.add_to_plot)

        self._create_plot_action = QAction("📈 Create New Plot", parent)
        self._create_plot_action.triggered.connect(self._actions.create_plot)

        self._export_menu = QMenu("💾 Export to", parent)
        self._export_hdf5_action = QAction("💾 Export to HDF5", parent)
        self._export_hdf5_action.triggered.connect(self._actions.export_hdf5)
        self._export_csv_action = QAction("📄 Export to CSV", parent)
        self._export_csv_action.triggered.connect(self._actions.export_csv)
        self._export_menu.addAction(self._export_hdf5_action)
        self._export_menu.addAction(self._export_csv_action)

        self._delete_action = QAction("🗑️ Delete", parent)
        self._delete_action.triggered.connect(self._actions.delete_item)

    def show_context_menu(self, position, index):
        if not index.isValid():
            return

        self._context_menu.clear()
        item_type = index.siblingAtColumn(0).data(Qt.ItemDataRole.UserRole + 1)

        if item_type == AssetType.TRACE:
            self._build_trace_menu()
        elif item_type == AssetType.DATASET:
            self._build_dataset_menu()

        self._context_menu.exec_(self._parent.mapToGlobal(position))

    def _build_dataset_menu(self):
        self._context_menu.addAction(self._add_dataset_action)
        self._context_menu.addMenu(self._add_data_menu)
        self._context_menu.addSeparator()
        self._context_menu.addAction(self._create_plot_action)
        self._context_menu.addAction(self._add_to_plot_action)
        self._context_menu.addSeparator()
        self._context_menu.addMenu(self._export_menu)
        self._context_menu.addSeparator()
        self._context_menu.addAction(self._delete_action)

    def _build_trace_menu(self):
        self._context_menu.addAction(self._create_plot_action)
        self._context_menu.addAction(self._add_to_plot_action)
        self._context_menu.addSeparator()
        self._context_menu.addMenu(self._export_menu)
        self._context_menu.addSeparator()
        self._context_menu.addAction(self._delete_action)