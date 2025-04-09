from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton

import src.util as util

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

def generate_html(main_win_root_dir, root_dir=''):
    """
    Generates HTML files from the results.
    """
    root_dir = root_dir if root_dir != '' else main_win_root_dir
    print("Generating HTML files...")
    try:
        util.generate_res_html(root_dir=root_dir)
    except Exception as e:
        print(f'Error generating HTML files:\n    {e}')

def generate_prof_html(main_win_root_dir, root_dir=''):
    """
    Generates professors data HTML file.
    """
    root_dir = root_dir if root_dir != '' else main_win_root_dir
    print("Generating professors data HTML file...")
    try:
        util.generate_prof_html(root_dir=root_dir)
    except Exception as e:
        print(f'Error generating professors data HTML file:\n    {e}')

def generate_subjects_html(main_win_root_dir, root_dir=''):
    """
    Generates subjects data HTML file.
    """
    root_dir = root_dir if root_dir != '' else main_win_root_dir
    print("Generating subjects data HTML file...")
    try:
        util.generate_subjects_html(root_dir=root_dir)
    except Exception as e:
        print(f'Error generating subjects data HTML file:\n    {e}')
