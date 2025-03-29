from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton

class PopupDialog(QDialog):
    def __init__(self, message, title="Warning", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.init_ui(message)

    def init_ui(self, message):
        layout = QVBoxLayout()

        label = QLabel(message)
        ok_button = QPushButton("OK")
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(ok_button)
        btn_layout.addStretch()
        ok_button.clicked.connect(self.accept)

        layout.addWidget(label)
        layout.addLayout(btn_layout)
        self.setLayout(layout)