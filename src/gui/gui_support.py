from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton

class PopupDialog(QDialog):
    def __init__(self, message, title="Warning", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.init_ui(message)

    def init_ui(self, message):
        layout = QVBoxLayout()

        label = QLabel(message)
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)

        layout.addWidget(label)
        layout.addWidget(ok_button)
        self.setLayout(layout)