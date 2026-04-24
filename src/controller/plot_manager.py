import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from src.core.structures import Dataset, LineConfig
from src.core.plot_object import PlotObject
from src.gui.plotting.plot_widget import PlotWindow
from PyQt5.QtCore import Qt

class PlotManager:
    def __init__(self, registry):
        self.registry = registry
        self.windows = {} # Store plot_id: PlotWindow instance

    def create_new_window(self, trace_ids):

        plot_id = f"plot_{len(self.windows):02d}"
        plot_obj = PlotObject(plot_id=plot_id, registry=self.registry)
        for tid in trace_ids:
            plot_obj.add_trace(tid)
            
        window = PlotWindow(plot_obj=plot_obj, plot_id=plot_id, plot_name=plot_id)
        
        self.windows[plot_id] = window
        window.setAttribute(Qt.WA_DeleteOnClose)
        window.destroyed.connect(lambda: self.windows.pop(plot_id, None))
        
        window.show()
        window.refresh()
        return window
    

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    manager = PlotManager(None)
    manager.create_new_window(trace_ids=["trace_01", "trace_02"])
    sys.exit(app.exec())