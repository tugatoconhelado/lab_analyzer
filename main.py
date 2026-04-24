import sys
from PyQt5.QtWidgets import QApplication
from src.gui.main_window import AnalyzerMainWindow
from src.core.engine import AnalysisEngine
from src.controller.bridge import AnalyzerBridge

def main():

    app = QApplication(sys.argv)

    window = AnalyzerMainWindow()
    controller = AnalyzerBridge(ui=window)

    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()