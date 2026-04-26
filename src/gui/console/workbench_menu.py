from dataclasses import dataclass
from typing import Callable

from PyQt5.QtCore import Qt, QModelIndex
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
    show_plot: Callable[[], None]
    export_png: Callable[[], None]
    export_svg: Callable[[], None]
    export_pdf: Callable[[], None]
    configure_plot: Callable[[], None]


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
        self._show_plot_action = QAction("👁️ Show Plot", parent)
        self._show_plot_action.triggered.connect(self._actions.show_plot)
        self._configure_plot_action = QAction("⚙️ Configure Plot", parent)
        self._configure_plot_action.triggered.connect(self._actions.configure_plot)

        self._export_menu = QMenu("💾 Export to", parent)
        self._export_hdf5_action = QAction("💾 Export to HDF5", parent)
        self._export_hdf5_action.triggered.connect(self._actions.export_hdf5)
        self._export_csv_action = QAction("📄 Export to CSV", parent)
        self._export_csv_action.triggered.connect(self._actions.export_csv)
        self._export_menu.addAction(self._export_hdf5_action)
        self._export_menu.addAction(self._export_csv_action)

        self._export_image_menu = QMenu("💾 Export Plot as Image", parent)
        self._export_png_action = QAction("🖼️ Export Plot to PNG", parent)
        self._export_png_action.triggered.connect(self._actions.export_png)
        self._export_image_menu.addAction(self._export_png_action)
        self._export_svg_action = QAction("🖼️ Export Plot to SVG", parent)
        self._export_svg_action.triggered.connect(self._actions.export_svg)
        self._export_image_menu.addAction(self._export_svg_action)
        self._export_pdf_action = QAction("🖼️ Export Plot to PDF", parent)
        self._export_pdf_action.triggered.connect(self._actions.export_pdf)
        self._export_image_menu.addAction(self._export_pdf_action)

        self._delete_action = QAction("🗑️ Delete", parent)
        self._delete_action.triggered.connect(self._actions.delete_item)

    def _get_root_index(self, index: QModelIndex) -> QModelIndex:
        node = index.sibling(index.row(), 0)
        while node.parent().isValid():
            node = node.parent()
        return node

    def _get_root_name(self, index: QModelIndex):
        root = self._get_root_index(index)
        return root.data(Qt.ItemDataRole.DisplayRole)

    def _get_container_index(self, index: QModelIndex) -> QModelIndex:
        """Return the direct parent row (column 0) that contains this item."""
        parent = index.sibling(index.row(), 0).parent()
        return parent.sibling(parent.row(), 0) if parent.isValid() else QModelIndex()

    def _get_item_type(self, index: QModelIndex) -> int:
        item_type = index.sibling(index.row(), 0).data(Qt.ItemDataRole.UserRole + 1)
        return int(item_type) if item_type is not None else 0

    def _can_delete_selection(self, index: QModelIndex) -> bool:
        selected_type = self._get_item_type(index)
        if selected_type & AssetType.LINK:
            return False

        container = self._get_container_index(index)
        if container.isValid():
            container_type = self._get_item_type(container)
            if container_type & AssetType.LINK:
                return False
        return True

    def show_context_menu(self, position, index):
        if not index.isValid():
            return

        self._context_menu.clear()
        item_type = self._get_item_type(index)
        can_delete = self._can_delete_selection(index)
        self._delete_action.setEnabled(can_delete)

        if item_type & AssetType.TRACE:
            self._build_trace_menu()
        elif item_type & AssetType.DATASET:
            self._build_dataset_menu()
        elif item_type & AssetType.PLOT:
            self._build_plot_menu()

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

    def _build_plot_menu(self):
        self._context_menu.addAction(self._configure_plot_action)
        self._context_menu.addAction(self._show_plot_action)
        self._context_menu.addSeparator()
        self._context_menu.addMenu(self._export_image_menu)
        self._context_menu.addSeparator()
        self._context_menu.addAction(self._delete_action)