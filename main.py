import sys
from PyQt5.QtWidgets import QApplication
from src.gui.main_window import AnalyzerMainWindow
from src.core.engine import AnalysisEngine
from src.gui.bridge import AnalyzerBridge


def main():

    app = QApplication(sys.argv)

    engine = AnalysisEngine(r"models")
    controller = AnalyzerBridge(engine)

    window = AnalyzerMainWindow(controller)
    window.show()
    window.connect_to_bridge()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()