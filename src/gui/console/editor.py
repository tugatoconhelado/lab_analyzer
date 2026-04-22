import os
import sys
from PyQt5.QtWidgets import QWidget
from PyQt5.uic import loadUi
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..',
                                            '..')))

from PyQt5.Qsci import QsciScintilla, QsciLexerPython
from PyQt5.QtGui import QFont, QColor, QPalette
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtCore import pyqtSlot as Slot


class EditorWidget(QsciScintilla):

    run_code_signal = Signal(str)  # Signal to send code to the console
    
    def __init__(self, parent=None):
        super().__init__(parent)
        loadUi(
            os.path.join('resources', 'ui', 'editor.ui'), self
        )

        self._setup_editor()
    def _setup_editor(self):

        self._lexer = QsciLexerPython(self)
        self.setLexer(self._lexer)
        
        BG_COLOR = QColor("#ffffff")     # Pure white or #fdfdfd for a softer feel
        TEXT_COLOR = QColor("#24292e")   # Deep charcoal/black
        KEYWORD_COLOR = QColor("#d73a49") # Crimson Red
        STRING_COLOR = QColor("#032f62")  # Deep Navy Blue
        COMMENT_COLOR = QColor("#6a737d") # Mid-range Grey
        NUMBER_COLOR = QColor("#005cc5")  # Bright Blue
        DECORATOR_COLOR = QColor("#6f42c1") # Purple

        # Apply Colors to the Lexer
        self._lexer.setDefaultColor(TEXT_COLOR)
        self._lexer.setPaper(BG_COLOR)

        # QScintilla uses 'Style IDs' for different parts of the code.
        # Style 0 is the default "everything else" text.
        self._lexer.setColor(TEXT_COLOR, 0) # Default text
        self._lexer.setColor(COMMENT_COLOR, QsciLexerPython.Comment)
        self._lexer.setColor(NUMBER_COLOR, QsciLexerPython.Number)
        self._lexer.setColor(STRING_COLOR, QsciLexerPython.DoubleQuotedString)
        self._lexer.setColor(STRING_COLOR, QsciLexerPython.SingleQuotedString)
        self._lexer.setColor(KEYWORD_COLOR, QsciLexerPython.Keyword)
        self._lexer.setColor(TEXT_COLOR, QsciLexerPython.Identifier)
        self._lexer.setColor(DECORATOR_COLOR, QsciLexerPython.Decorator)
        
        self.setMarginType(0, QsciScintilla.NumberMargin)
        self.setMarginWidth(0, "0000")
        self.setMarginsBackgroundColor(QColor("#f6f8fa"))
        self.setMarginsForegroundColor(QColor("#1b1f23"))
        self.setMarginLineNumbers(0, True)

        # Cell Highlighting logic
        self.setCaretForegroundColor(QColor("black"))
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QColor("#f6f8fa"))
        self.setEdgeMode(QsciScintilla.EdgeLine)
        self.setEdgeColumn(80) # Scientific standard line limit

        self.setSelectionBackgroundColor(QColor("#c8e1ff"))

        font = QFont("Consolas", 11)
        self._lexer.setDefaultFont(font)
        
        # Indentation
        self.setIndentationsUseTabs(False)
        self.setIndentationWidth(4)
        self.setAutoIndent(True)

    def get_current_cell_code(self):
        """Finds text between # %% markers based on cursor position."""
        all_text = self.text()
        lines = all_text.splitlines()

        if not lines:
            return ""
        
        current_row, _ = self.getCursorPosition()
        row = current_row if current_row is not None else 0
        search_index = max(0, min(row, len(lines) - 1))
        
        start_row = 0
        end_row = len(lines)

        # Look backwards for start of cell
        for r in range(search_index, -1, -1):
            if lines[r].strip().startswith("# %%"):
                start_row = r + 1
                break
        
        # Look forwards for end of cell
        for r in range(search_index + 1, len(lines)):
            if lines[r].strip().startswith("# %%"):
                end_row = r
                break
        
        return "\n".join(lines[start_row:end_row])

    def keyPressEvent(self, e):
        # Shift + Enter to run the cell
        if e is None:
            return
        if e.key() == Qt.Key.Key_Return and e.modifiers() == Qt.KeyboardModifier.ShiftModifier:
            code = self.get_current_cell_code()
            # Send this 'code' string to your Jupyter Kernel Client!
            print(f"Sending Cell:\n{code}") 
            self.run_code_signal.emit(code)
        else:
            super().keyPressEvent(e)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    widget = EditorWidget()
    widget.show()
    sys.exit(app.exec())