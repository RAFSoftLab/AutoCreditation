import json
from pathlib import Path
import re
import subprocess
import sys
import os
import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QSystemTrayIcon, QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QTreeView, QFileSystemModel, QSplitter, QLabel, QPushButton, QLineEdit,
    QStackedWidget, QTextBrowser, QFileDialog, QListWidgetItem
)
from PyQt5.QtCore import Qt
from pyqtspinner.spinner import WaitingSpinner

# sys.path.append(os.getcwd())

import src.util as util


class FileExplorer(QMainWindow):

    def __init__(self, root_dir=''):
        super().__init__()

        self.root_dir = os.getcwd() if root_dir == '' else root_dir
        self.gen_tree = ''
        self.side_bar_items = ["Results", "  Documentation Tree", "  Final Results", "  Professors", "  Subjects", "File Explorer"]
        self.current_view = 'Results'
        self.dir_name = os.path.dirname(__file__)

        self.setWindowTitle("Dashboard File Explorer")
        self.setGeometry(200, 100, 1000, 600)  # Initial size, but not fixed
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(os.path.join(self.dir_name, Path("resources/raf_logo_win.png"))), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.setWindowIcon(icon)
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setIcon(icon)

        # Main Layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Sidebar
        self.sidebar = QListWidget()
        for item in self.side_bar_items:
            item_elem = QListWidgetItem()
            item_elem.setText(item)
            if item in ["Results", "File Explorer"]:
                item_font = item_elem.font()
                item_font.setBold(True)
                item_elem.setFont(item_font)
            self.sidebar.addItem(item_elem)
        self.sidebar.itemClicked.connect(self.switch_panel)

        # Stacked Widget (For Switching Between Views)
        self.stack = QStackedWidget()

        # Explorer Panel (Tree View)
        self.model = QFileSystemModel()
        self.model.setRootPath(os.path.expanduser("~"))
        self.file_view = QTreeView()
        self.file_view.setModel(self.model)
        if not os.path.exists(os.path.join(self.root_dir, Path('tmp/input_files'))):
            self.file_view.setRootIndex(self.model.index(os.path.expanduser("~")))
        else:
            self.file_view.setRootIndex(self.model.index(os.path.join(self.root_dir, Path('tmp/input_files'))))
        self.file_view.doubleClicked.connect(self.open_item)

        # Results Panel (HTML Viewer with QTextEdit)
        self.html_viewer = QTextBrowser()
        self.html_viewer.setReadOnly(True)
        self.html_viewer.setHtml(f"<h2>Results & File Explorer</h2><p>Choose option from side panel - view results or explore documentation files.</p>")  # Default HTML file
        self.html_viewer.anchorClicked.connect(self.open_link)
        self.html_viewer.setOpenLinks(False)

        # Adding Panels to Stack
        explorer_widget = QWidget()
        explorer_layout = QVBoxLayout()
        explorer_layout.addWidget(self.file_view)
        explorer_widget.setLayout(explorer_layout)

        self.stack.addWidget(self.html_viewer)  # Index 0: Results Panel
        self.stack.addWidget(explorer_widget)  # Index 1: Explorer

        # Top Bar (Navigation for Explorer)
        self.top_bar = QHBoxLayout()
        self.path_input = QLineEdit(os.path.expanduser("~"))
        if os.path.exists(os.path.join(self.root_dir, Path('tmp/input_files'))):
            self.path_input.setText(os.path.join(self.root_dir, Path('tmp/input_files')))
        self.go_button = QPushButton("Go")
        self.browse_button = QPushButton("Browse")

        self.go_button.clicked.connect(self.navigate_to_input_path)
        self.browse_button.clicked.connect(self.browse_for_folder)

        self.top_bar.addWidget(QLabel("Path:"))
        self.top_bar.addWidget(self.path_input)
        self.top_bar.addWidget(self.go_button)
        self.top_bar.addWidget(self.browse_button)

        # Splitter for Sidebar & Main Area (Makes Layout Responsive)
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.stack)
        self.splitter.setStretchFactor(1, 2)  # Sidebar stays smaller, Main Area stretches

        # Main Layout
        main_layout.addLayout(self.top_bar)
        main_layout.addWidget(self.splitter)

        # Default to "Explorer"
        self.sidebar.setCurrentRow(0)  # Set default selection to Explorer
        self.stack.setCurrentIndex(0)  # Show Explorer Panel

        # Running spinner
        self.running_spinner = WaitingSpinner(self.html_viewer, True, True, Qt.ApplicationModal)

    def switch_panel(self, item=''):
        """
        Swich between file explorer and different HTML views.

        Args:
            item (str):     Name of the item clicked.
        Returns:
            None
        """
        text = item.text().strip()
        if text == "File Explorer":
            self.stack.setCurrentIndex(1)  # Show File Explorer
            self.current_view = 'File Explorer'
        elif text in ["Results", ""]:  # Results Panel
            self.sidebar.setCurrentRow(self.sidebar.currentRow() + 1)  # Move to Documentation Tree
            self.load_documentation_tree()
            self.stack.setCurrentIndex(0)  # Show Results Panel
            self.current_view = 'Results'
        elif text == "Documentation Tree":
            self.load_documentation_tree()
            self.stack.setCurrentIndex(0)  # Show Results Panel
            self.current_view = 'Documentation Tree'
        elif text == "Final Results":
            self.load_html_content("results/results.html")
            self.stack.setCurrentIndex(0)
            self.current_view = 'Final Results'
        elif text == "Professors":
            self.load_html_content("results/professors_data.html")
            self.stack.setCurrentIndex(0)
            self.current_view = 'Professors'
        elif text == "Subjects":
            self.load_html_content("results/subjects_data.html")
            self.stack.setCurrentIndex(0)
            self.current_view = 'Subjects'

    def load_documentation_tree(self):
        """
        Loads the documentation tree.
        """
        documentation_structure = self.gen_tree
        if documentation_structure != '':
            self.html_viewer.setHtml(f"<h2>Documentation structure</h2><pre>{documentation_structure}</pre>")
        elif not os.path.exists(os.path.join(self.root_dir, Path('tmp/input_files'))):
            documentation_structure = "Documentation tree could not be generated - no input files found."
            self.html_viewer.setHtml(f"<h2>Documentation structure</h2><p>{documentation_structure}</p>")
        else:
            self.generate_documentation_tree()

    def load_html_content(self, filename, root_dir=''):
        """
        Loads content from a locally generated HTML file into QTextEdit.

        Args:
            filename (str):     Relative path of the file - relative to the tmp directory.
            root_dir (str):     Root directory of the file, absolute path.
        Returns:
            None
        """
        file_path = os.path.join(self.root_dir if root_dir == '' else root_dir, Path(f"tmp/{filename}"))
        try:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as file:
                    html_content = file.read()
                self.html_viewer.setHtml(html_content)
            elif filename.endswith('.html') and os.path.exists(os.path.join(self.root_dir if root_dir == '' else root_dir, Path(f"tmp/{filename[:-5]}.json"))):
                with open(os.path.join(self.root_dir if root_dir == '' else root_dir, Path(f"tmp/{filename[:-5]}.json")), "r", encoding="utf-8") as file:
                    html_content = json.load(file)
                self.html_viewer.setHtml(f"<pre>{json.dumps(html_content, indent=4, ensure_ascii=False)}</pre>")
            elif filename.endswith('.html') and os.path.exists(os.path.join(self.root_dir if root_dir == '' else root_dir, Path(f"tmp/{filename.split(os.sep if re.search(re.escape(os.sep), filename) else '/')[-1][:-5]}.json"))):
                with open(os.path.join(self.root_dir if root_dir == '' else root_dir, Path(f"tmp/{filename.split(os.sep if re.search(re.escape(os.sep), filename) else '/')[-1][:-5]}.json")), "r", encoding="utf-8") as file:
                    html_content = json.load(file)
            else:
                self.html_viewer.setHtml(f"<h2>No data found</h2><p>{filename} is missing.</p>")
        except Exception as e:
            print(f'Error loading file:\n    {e}')
            self.html_viewer.setHtml(f"<h2>Error loading file</h2><p>{filename} is missing.</p>")

    def navigate_to_input_path(self):
        """
        Navigate to manually entered path.
        """
        path = self.path_input.text()
        if os.path.exists(path):
            self.file_view.setRootIndex(self.model.index(path))

    def browse_for_folder(self):
        """
        Open a dialog to select a folder.
        """
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder", os.path.expanduser("~"))
        if folder_path:
            self.path_input.setText(folder_path)
            self.file_view.setRootIndex(self.model.index(folder_path))

    def open_item(self, index):
        """
        Open a file or navigate into a folder.

        Args:
            index (str):     Index of the item clicked (file or folder to open).
        Returns:
            None
        """
        path = self.model.filePath(index)
        if os.path.isdir(path):
            self.file_view.setRootIndex(self.model.index(path))
            self.path_input.setText(path)
        else:
            # os.startfile(path)  # Opens file with default application
            if sys.platform == "Windows":
                os.startfile(path)
            else:
                opener = "open" if sys.platform == "darwin" else "xdg-open"
                subprocess.call([opener, path])

    @QtCore.pyqtSlot(str)
    def load_gen_tree(self, gen_tree):
        """
        Loads the generated documentation tree.

        Args:
            gen_tree (str):     Generated documentation tree
        Returns:
            None
        """
        self.gen_tree = gen_tree
        self.load_documentation_tree()
        self.running_spinner.stop()

    def generate_documentation_tree(self):
        """
        Generates the documentation tree, in a separate thread.
        """
        self.running_spinner.start()
        self.html_viewer.setHtml(f"<h2>Generating documentation tree...</h2><p>Please wait...</p>")
        self.thread = QtCore.QThread()
        self.worker = Worker(root_dir=self.root_dir)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.generated_tree.connect(self.thread.quit)
        self.worker.generated_tree.connect(self.load_gen_tree)
        self.thread.start()

    def open_link(self, link):
        """
        Opens data represented by the given link in a new window.

        Args:
            link (str):     Link to the data.
        Returns:
            None
        """
        try:
            if self.current_view in ['Professors', 'Subjects']:
                data_file = Path('tmp/professors_data.json')
                with open(os.path.join(self.root_dir, data_file), "r", encoding="utf-8") as file:
                    data = json.load(file)
                try:
                    table_data = [i for i in data if 'type' in i.keys() and i['type'] == 'prof_tables'][0]['data']
                except Exception as e:
                    table_data = []
                for item in table_data:
                    if str(item['table_key']) != link.toString():
                        continue
                    subj_html = util.generate_prof_subject_html(root_dir=self.root_dir, subjects_data=item)
                    self.new_window = TableWindow(dir_name=self.dir_name, table_html=subj_html)
                    self.new_window.setWindowTitle(f"Professor: {item['name']}")
                    self.new_window.show()
                    break
            elif self.current_view == 'Final Results':
                data_file = Path('tmp/results/results.json')
                with open(os.path.join(self.root_dir, data_file), "r", encoding="utf-8") as file:
                    data = json.load(file)
                # No links in final results view
        except Exception as e:
            print(f'Error loading file:\n    {e}')
            self.html_viewer.setHtml(f"<h2>Error loading data</h2><p>{data_file} is missing or invalid.</p>")
            return

class Worker(QtCore.QObject):
    """
    Worker class for generating the documentation tree.
    """

    generated_tree = QtCore.pyqtSignal(str)

    def __init__(self, root_dir=''):
        super(Worker, self).__init__()

        self.root_dir = os.getcwd() if root_dir == '' else root_dir

    def run(self):
        gen_tree = util.tree(dir_path=os.path.join(self.root_dir, Path('tmp/input_files')))
        self.generated_tree.emit(gen_tree)

class TableWindow(QWidget):
    """
    Window for displaying HTML tables.
    """
    def __init__(self, parent=None, dir_name='', table_html=''):
        super(TableWindow, self).__init__(parent)
        self.setGeometry(250, 150, 1000, 600)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(os.path.join(dir_name, Path("resources/raf_logo_win.png"))), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.setWindowIcon(icon)
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setIcon(icon)
        self.initUI(table_html=table_html)

    def initUI(self, table_html=''):
        self.layout = QVBoxLayout()
        self.table_view = QTextBrowser()
        self.table_view.setReadOnly(True)
        self.table_view.setHtml(table_html)
        self.layout.addWidget(self.table_view)
        self.setLayout(self.layout)
        self.setWindowModality(Qt.ApplicationModal)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key.Key_Escape:
            self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileExplorer()
    window.show()
    sys.exit(app.exec())
