import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from PyQt5.QtWidgets import QHeaderView, QTreeView
from PyQt5.QtCore import Qt, pyqtSignal as Signal, pyqtSlot as Slot

from src.core.structures import WorkbenchAsset
from src.core.constants import AssetType
from src.gui.console.workbench_model import WorkbenchModel
from src.gui.console.workbench_menu import WorkbenchMenuActions, WorkbenchMenuHelper


class WorkbenchExplorer(QTreeView):

    create_new_trace_sig = Signal(list)
    add_to_trace_sig = Signal(list)
    create_plot_sig = Signal(list)
    add_to_plot_sig = Signal(list)
    export_hdf5_sig = Signal(list)
    export_csv_sig = Signal(list)
    show_plot_sig = Signal(list)
    export_plot_sig = Signal(list, str)
    delete_item_sig = Signal(list)
    configure_plot_sig = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._added_items = 0

        # 1. Create the Model
        self._model = WorkbenchModel(None)
        self.setModel(self._model)
        
        # 2. Setup visual behavior
        header = self.header()
        if header is not None:
            header.setSectionResizeMode(0, QHeaderView.Stretch) # Column 0 adjusts to text
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  
            header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  
        width = 600
        self.setEditTriggers(QTreeView.NoEditTriggers) # Read-only
        self.setSelectionBehavior(QTreeView.SelectRows)
        self.setSelectionMode(self.ExtendedSelection)

        self._menu_helper = WorkbenchMenuHelper(
            self,
            WorkbenchMenuActions(
                create_new_trace=self._emit_create_new_trace,
                add_to_trace=self._emit_add_to_trace,
                create_plot=self._emit_create_plot,
                add_to_plot=self._emit_add_to_plot,
                export_hdf5=self._emit_export_hdf5,
                export_csv=self._emit_export_csv,
                delete_item=self._emit_delete_item,
                show_plot=self._emit_show_plot,
                export_png=self._emit_export_png,
                export_svg=self._emit_export_svg,
                export_pdf=self._emit_export_pdf,
                configure_plot=self._emit_configure_plot,
            ),
        )
        
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.doubleClicked.connect(self.on_item_double_clicked)
        
        self.expandAll() # Keep folders open by default

    def show_context_menu(self, position):
        self._menu_helper.show_context_menu(position, self.indexAt(position))

    def on_item_double_clicked(self, index):
        item = self._model.itemFromIndex(index)
        if item is None:
            return
        kind = item.data(Qt.ItemDataRole.UserRole + 1)
        if kind is None:
            return
        if kind & AssetType.LINK:
            print("Double-clicked link on item:", item.text())
            link_target = item.data(Qt.ItemDataRole.UserRole + 2)

            if not link_target:
                return
            
            linked_index = self._model.find_linked_item_idx(link_target)

            if linked_index is not None:
                self.setCurrentIndex(linked_index)
        
        elif kind & AssetType.DATASET:
            asset = item.data(Qt.ItemDataRole.UserRole + 3)
            if asset is not None:
                print(f"Double-clicked dataset: {asset}")

        elif kind & AssetType.TRACE:
            asset = item.data(Qt.ItemDataRole.UserRole + 3)
            if asset is not None:
                print(f"Double-clicked trace: {asset}")

    def _selected_assets(self):
        assets = []
        selection_model = self.selectionModel()
        if selection_model is None:
            return assets
        for index in selection_model.selectedRows():
            asset = index.data(Qt.ItemDataRole.UserRole)
            kind = index.data(Qt.ItemDataRole.UserRole + 1)
            if asset is not None:
                assets.append(asset)
        return assets

    def _emit_selected_assets(self, signal):
        signal.emit(self._selected_assets())

    def _emit_create_new_trace(self):
        self._emit_selected_assets(self.create_new_trace_sig)

    def _emit_add_to_trace(self):
        self._emit_selected_assets(self.add_to_trace_sig)

    def _emit_create_plot(self):
        self._emit_selected_assets(self.create_plot_sig)

    def _emit_add_to_plot(self):
        self._emit_selected_assets(self.add_to_plot_sig)

    def _emit_export_hdf5(self):
        self._emit_selected_assets(self.export_hdf5_sig)

    def _emit_export_csv(self):
        self._emit_selected_assets(self.export_csv_sig)

    def _emit_delete_item(self):
        self._emit_selected_assets(self.delete_item_sig)

    def _emit_show_plot(self):
        self._emit_selected_assets(self.show_plot_sig)

    def _emit_export_plot(self, export_format: str):
        plot_id = self._selected_assets()
        if not plot_id:
            return
        self.export_plot_sig.emit(plot_id, export_format)

    def _emit_export_png(self):
        self._emit_export_plot("png")

    def _emit_export_svg(self):
        self._emit_export_plot("svg")

    def _emit_export_pdf(self):
        self._emit_export_plot("pdf")
    
    def _emit_configure_plot(self):
        self._emit_selected_assets(self.configure_plot_sig)

        
        
if __name__ == "__main__":

    from PyQt5.QtWidgets import QApplication
    from qtconsole.inprocess import QtInProcessKernelManager
    from src.core.structures import Dataset, Trace
    from src.core.plot_object import PlotObject
    import numpy as np
    from src.gui.console.workspace import WorkspaceWidget
    
    app = QApplication(sys.argv)
    kernel_manager = QtInProcessKernelManager()
    kernel_manager.start_kernel()
    kernel_client = kernel_manager.client()
    kernel_client.start_channels()
    widget = WorkspaceWidget(None, kernel_manager, kernel_client)
    x_ds_test1 = Dataset(name="X Data", data=np.random.random(100), asset_id=1)
    y_ds_test1 = Dataset(name="Y Data", data=np.random.random(100), asset_id=2)
    test_trace = Trace(name="Test Trace", x_ds=x_ds_test1, y_ds=y_ds_test1, asset_id=6)
    widget.workbench._model.add_item(x_ds_test1)
    widget.workbench._model.add_item(y_ds_test1)
    widget.workbench._model.add_item(test_trace)
    widget.workbench._model.add_item(Dataset(name="Test Dataset", data=np.array([1, 2, 3]), asset_id=3))
    widget.workbench._model.add_item(Dataset(name="Var3 Dataset", data=np.array([4, 5, 6]), asset_id=4))
    plot_test = PlotObject("Test Plot", widget.workbench._model.registry, asset_id=5)
    plot_test.traces[6] = test_trace

    widget.workbench._model.add_item(plot_test)
    widget.resize(800, 600)
    widget.show()
    widget.raise_()
    widget.activateWindow()
    sys.exit(app.exec())