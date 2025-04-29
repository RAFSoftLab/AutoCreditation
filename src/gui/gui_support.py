import os
from pathlib import Path
import re
import ujson as json
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
import PyQt5.QtGui as QtGui

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

def load_html_content(viewer_widget, filename, root_dir):
    """
    Loads content from a locally generated HTML file into QTextEdit.

    Args:
        viewer_widget (QWidget):     Viewer widget to load content into.
        filename (str):              Relative path of the file - relative to the tmp directory.
        root_dir (str):              Root directory of the file, absolute path.
    Returns:
        None
    """
    file_path = os.path.join(root_dir if root_dir == '' else root_dir, Path(f"tmp/{filename}"))
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                html_content = file.read()
            viewer_widget.setHtml(html_content)
        elif filename.endswith('.html') and os.path.exists(os.path.join(root_dir if root_dir == '' else root_dir, Path(f"tmp/{filename[:-5]}.json"))):
            with open(os.path.join(root_dir if root_dir == '' else root_dir, Path(f"tmp/{filename[:-5]}.json")), "r", encoding="utf-8") as file:
                html_content = json.load(file)
            viewer_widget.setHtml(f"<pre>{json.dumps(html_content, indent=4, ensure_ascii=False)}</pre>")
        elif filename.endswith('.html') and os.path.exists(os.path.join(root_dir if root_dir == '' else root_dir, Path(f"tmp/{filename.split(os.sep if re.search(re.escape(os.sep), filename) else '/')[-1][:-5]}.json"))):
            with open(os.path.join(root_dir if root_dir == '' else root_dir, Path(f"tmp/{filename.split(os.sep if re.search(re.escape(os.sep), filename) else '/')[-1][:-5]}.json")), "r", encoding="utf-8") as file:
                html_content = json.load(file)
        else:
            viewer_widget.setHtml(f"<h2>No data found</h2><p>{filename} is missing.</p>")
    except Exception as e:
        print(f'Error loading file:\n    {e}')
        viewer_widget.setHtml(f"<h2>Error loading file</h2><p>{filename} is missing.</p>")

def create_icon(icon_name):
    """
    Creates an icon from the given icon name and path.

    Args:
        icon_name (str):     Name of the icon.
    Returns:
        QIcon:    Created icon.
    """
    icon = QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap(os.path.join(os.path.dirname(__file__), Path(f'resources/icons/{icon_name}.png'))), QtGui.QIcon.Normal, QtGui.QIcon.On)
    return icon
