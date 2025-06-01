import os
from pathlib import Path
import re
import subprocess
import sys
import ujson as json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QPushButton, QLabel, QTabWidget,
                            QFrame, QSizePolicy, QStackedWidget, QSystemTrayIcon,
                            QTreeView, QFileDialog, QFileSystemModel, QTextBrowser)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, QSize
from PyQt5 import QtCore
import PyQt5.QtGui as QtGui
from PyQt5.QtGui import QIcon, QFont
from pyqtspinner.spinner import WaitingSpinner

# Testing only:
# sys.path.append(os.getcwd())

import src.gui.gui_support as gui_support
import src.util as util
import src.overview_and_statistics_gen as overview_and_statistics_gen


class FileExplorer(QMainWindow):
    def __init__(self, root_dir=''):
        super().__init__()
        self.setWindowTitle("AutoCreditation Viewer")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(os.path.join(os.path.dirname(__file__), Path("resources/raf_logo_win.png"))), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.setWindowIcon(icon)
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setIcon(icon)
        self.setMinimumSize(1000, 600)

        self.gen_tree = ''

        self.root_dir = os.getcwd() if root_dir == '' else root_dir

        try:
            self.analizer = overview_and_statistics_gen.AcademicDataAnalyzer(prof_data=util.load_json(os.path.join(self.root_dir, Path('tmp/professors_data.json'))), subj_data=util.load_json(os.path.join(self.root_dir, Path('tmp/subjects_data.json'))))
        except Exception as e:
            print(f'Error loading data:\n    {e}')
            self.analizer = None

        # Running spinner
        # self.running_spinner = WaitingSpinner(self.html_viewer, True, True, Qt.ApplicationModal)

        # Initialize the UI
        self.init_ui()

    def init_ui(self):
        # Main central widget and layout
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setCentralWidget(central_widget)

        # Create sidebar
        self.sidebar = self.create_sidebar()
        main_layout.addWidget(self.sidebar)

        # Create content area (stacked widget to switch between different content)
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack)

        # Set stretch factor to make content area use more space
        main_layout.setStretchFactor(self.sidebar, 0)
        main_layout.setStretchFactor(self.content_stack, 4)

        # Create different content widgets for each sidebar option
        self.create_dashboard_widget()
        self.create_results_widget()
        self.create_professor_widget()
        self.create_subject_widget()
        self.create_explorer_widget()

        # Set default to Dashboard
        self.sidebar.findChild(QPushButton, "dashboard_btn").setStyleSheet(
            "QPushButton { background-color: #3a7ebf; color: white; text-align: left; padding: 10px; border: none; }"
        )
        self.content_stack.setCurrentIndex(0)
        self.dashboard_tab_changed(0)
        self.showMaximized()

    def create_sidebar(self):
        # Create sidebar frame
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setStyleSheet("""
            #sidebar {
                background-color: #2c3e50;
                min-width: 200px;
                max-width: 200px;
            }
            QPushButton {
                background-color: #2c3e50;
                color: white;
                text-align: left;
                padding: 10px;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
        """)

        # Create sidebar layout
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Create logo or app name area
        app_name = QLabel("AutoCreditation")
        app_name.setAlignment(Qt.AlignCenter)
        app_name.setStyleSheet("color: white; font-size: 18px; font-weight: bold; padding: 20px;")
        sidebar_layout.addWidget(app_name)

        # Add sidebar buttons

        dashboard_btn = QPushButton("Overview")
        dashboard_btn.setObjectName("dashboard_btn")
        dashboard_btn.setIcon(gui_support.create_icon('home'))
        dashboard_btn.clicked.connect(lambda: self.show_content(0, dashboard_btn))

        results_btn = QPushButton("Results")
        results_btn.setObjectName("results_btn")
        results_btn.setIcon(gui_support.create_icon('bar'))
        results_btn.clicked.connect(lambda: self.show_content(1, results_btn))

        professors_btn = QPushButton("Professors")
        professors_btn.setObjectName("professors_btn")
        professors_btn.setIcon(gui_support.create_icon('group-profile-users'))
        professors_btn.clicked.connect(lambda: self.show_content(2, professors_btn))

        subjects_btn = QPushButton("Subjects")
        subjects_btn.setObjectName("subjects_btn")
        subjects_btn.setIcon(gui_support.create_icon('book'))
        subjects_btn.clicked.connect(lambda: self.show_content(3, subjects_btn))

        explorer_btn = QPushButton("Explorer")
        explorer_btn.setObjectName("explorer_btn")
        explorer_btn.setIcon(gui_support.create_icon('folder'))
        explorer_btn.clicked.connect(lambda: self.show_content(4, explorer_btn))

        sidebar_layout.addWidget(dashboard_btn)
        sidebar_layout.addWidget(results_btn)
        sidebar_layout.addWidget(professors_btn)
        sidebar_layout.addWidget(subjects_btn)
        sidebar_layout.addWidget(explorer_btn)

        # Add stretcher to push settings to bottom if desired
        sidebar_layout.addStretch()

        return sidebar

    def create_dashboard_widget(self):
        # Dashboard container with top bar and content area organized as tabs
        dashboard_container = QWidget()
        dashboard_layout = QVBoxLayout(dashboard_container)
        dashboard_layout.setContentsMargins(0, 0, 0, 0)

        # Top bar for Dashboard
        topbar = QFrame()
        topbar.setStyleSheet("background-color: #f0f0f0; border-bottom: 1px solid #ddd;")
        topbar_layout = QHBoxLayout(topbar)

        dashboard_label = QLabel("Documentation Overview")
        dashboard_label.setFont(QFont("Arial", 14, QFont.Bold))
        topbar_layout.addWidget(dashboard_label)

        dashboard_layout.addWidget(topbar)

        # Tab widget for main content
        tab_widget = QTabWidget()

        # Add tabs to the tab widget
        summary_tab = QWidget()
        stats_tab = QWidget()

        # Add content to each tab (simplified here)
        summary_layout = QVBoxLayout(summary_tab)
        self.summary_viewer = QWebEngineView()
        summary_layout.addWidget(self.summary_viewer)

        stats_layout = QVBoxLayout(stats_tab)
        self.stats_viewer = QWebEngineView()
        stats_layout.addWidget(self.stats_viewer)

        tab_widget.addTab(summary_tab, "Summary")
        tab_widget.addTab(stats_tab, "Statistics")
        tab_widget.currentChanged.connect(self.dashboard_tab_changed)

        dashboard_layout.addWidget(tab_widget)

        self.content_stack.addWidget(dashboard_container)

    @QtCore.pyqtSlot(int)
    def dashboard_tab_changed(self, index):
        if index == 0:
            if not self.analizer:
                self.summary_viewer.setHtml("<h2>No data loaded</h2>")
            self.summary_viewer.setHtml(self.analizer.generate_overview())
        elif index == 1:
            if not self.analizer:
                self.stats_viewer.setHtml("<h2>No data loaded</h2>")
            self.stats_viewer.setHtml(self.analizer.generate_statistics())

    def create_results_widget(self):
        # Tasks container with top bar and content area
        results_container = QWidget()
        reuslts_layout = QVBoxLayout(results_container)
        reuslts_layout.setContentsMargins(0, 0, 0, 0)

        # Top bar for Tasks
        topbar = QFrame()
        topbar.setStyleSheet("background-color: #f0f0f0; border-bottom: 1px solid #ddd;")
        topbar_layout = QHBoxLayout(topbar)

        results_label = QLabel("Results View")
        results_label.setFont(QFont("Arial", 14, QFont.Bold))
        topbar_layout.addWidget(results_label)

        topbar_layout.addStretch()

        reuslts_layout.addWidget(topbar)

        # Tab widget for task views
        tab_widget = QTabWidget()

        # Add tabs to the tab widget
        results_tab = QWidget()
        doc_tree = QWidget()

        # Add content to each tab (simplified here)
        results_layout = QVBoxLayout(results_tab)
        self.results_viewer = QTextBrowser()
        results_layout.addWidget(self.results_viewer)
        tree_layout = QVBoxLayout(doc_tree)
        self.tree_viewer = QTextBrowser()
        tree_layout.addWidget(self.tree_viewer)

        in_progress_layout = QVBoxLayout(doc_tree)
        in_progress_layout.addWidget(QLabel("Documentation Tree"))

        tab_widget.addTab(results_tab, "Results")
        tab_widget.addTab(doc_tree, "Documentation Tree")
        tab_widget.currentChanged.connect(self.res_tab_changed)

        reuslts_layout.addWidget(tab_widget)

        self.content_stack.addWidget(results_container)

    @QtCore.pyqtSlot(int)
    def res_tab_changed(self, index):
        if index == 0:
            gui_support.load_html_content(self.results_viewer, "results/results.html", self.root_dir)
        elif index == 1:
            self.load_documentation_tree(self.tree_viewer)

    def create_professor_widget(self):
        # Projects container with top bar and content area
        professor_container = QWidget()
        professor_layout = QVBoxLayout(professor_container)
        professor_layout.setContentsMargins(0, 0, 0, 0)

        # Top bar for Projects
        topbar = QFrame()
        topbar.setStyleSheet("background-color: #f0f0f0; border-bottom: 1px solid #ddd;")
        topbar_layout = QHBoxLayout(topbar)

        professors_label = QLabel("Professors Data")
        professors_label.setFont(QFont("Arial", 14, QFont.Bold))
        topbar_layout.addWidget(professors_label)

        topbar_layout.addStretch()

        professor_layout.addWidget(topbar)

        # Tab widget for project views
        tab_widget = QTabWidget()

        # Add tabs to the tab widget
        professor_view = QWidget()
        professor_table = QWidget()

        professor_view_layout = QVBoxLayout(professor_view)
        self.professor_view_viewer = QTextBrowser()
        professor_view_layout.addWidget(self.professor_view_viewer)
        self.professor_view_viewer.anchorClicked.connect(self.open_link)
        self.professor_view_viewer.setOpenLinks(False)

        professor_table_layout = QVBoxLayout(professor_table)
        self.professor_table_viewer = gui_support.DatabaseTableWidget()
        self.professor_table_viewer.set_table_data(os.path.join(self.root_dir, Path('tmp/acreditation.db')), "professors_table")
        professor_table_layout.addWidget(self.professor_table_viewer)

        tab_widget.addTab(professor_view, "View")
        tab_widget.addTab(professor_table, "Table")
        tab_widget.currentChanged.connect(self.prof_tab_changed)

        professor_layout.addWidget(tab_widget)

        self.content_stack.addWidget(professor_container)

    @QtCore.pyqtSlot(int)
    def prof_tab_changed(self, index):
        if index == 0:
            gui_support.load_html_content(self.professor_view_viewer, "results/professors_data.html", self.root_dir)
        elif index == 1:
            print("Table viewer")

    def create_subject_widget(self):
        # Settings container with top bar and content area
        subject_container = QWidget()
        subject_layout = QVBoxLayout(subject_container)
        subject_layout.setContentsMargins(0, 0, 0, 0)

        # Top bar for Settings
        topbar = QFrame()
        topbar.setStyleSheet("background-color: #f0f0f0; border-bottom: 1px solid #ddd;")
        topbar_layout = QHBoxLayout(topbar)

        subject_label = QLabel("Subjects Data")
        subject_label.setFont(QFont("Arial", 14, QFont.Bold))
        topbar_layout.addWidget(subject_label)

        topbar_layout.addStretch()

        subject_layout.addWidget(topbar)

        # Tab widget for settings categories
        tab_widget = QTabWidget()

        # Add tabs to the tab widget
        subject_view = QWidget()
        subject_table = QWidget()

        # Add content to each tab (simplified here)
        subject_view_layout = QVBoxLayout(subject_view)
        self.subject_view_viewer = QTextBrowser()
        subject_view_layout.addWidget(self.subject_view_viewer)
        self.subject_view_viewer.anchorClicked.connect(self.open_link)
        self.subject_view_viewer.setOpenLinks(False)

        subject_table_layout = QVBoxLayout(subject_table)
        self.subject_table_viewer = QTextBrowser()
        self.subject_table_viewer = gui_support.DatabaseTableWidget()
        self.subject_table_viewer.set_table_data(os.path.join(self.root_dir, Path('tmp/acreditation.db')), "subjects_table")
        subject_table_layout.addWidget(self.subject_table_viewer)

        tab_widget.addTab(subject_view, "View")
        tab_widget.addTab(subject_table, "Table")
        tab_widget.currentChanged.connect(self.subj_tab_changed)

        subject_layout.addWidget(tab_widget)

        self.content_stack.addWidget(subject_container)

    @QtCore.pyqtSlot(int)
    def subj_tab_changed(self, index):
        if index == 0:
            gui_support.load_html_content(self.subject_view_viewer, "results/subjects_data.html", self.root_dir)
        elif index == 1:
            print("Table viewer")

    def create_explorer_widget(self):
        # Settings container with top bar and content area
        explorer_container = QWidget()
        explorer_layout = QVBoxLayout(explorer_container)
        explorer_layout.setContentsMargins(0, 0, 0, 0)

        # Top bar for Settings
        topbar = QFrame()
        topbar.setStyleSheet("background-color: #f0f0f0; border-bottom: 1px solid #ddd;")
        topbar_layout = QHBoxLayout(topbar)

        explorer_label = QLabel("File Explorer")
        explorer_label.setFont(QFont("Arial", 14, QFont.Bold))
        topbar_layout.addWidget(explorer_label)

        # Add save and reset buttons
        root_btn = QPushButton("Set Root Directory")
        root_btn.setStyleSheet("background-color: #2c3e50; color: white; padding: 5px 10px; border: none;")
        root_btn.clicked.connect(self.set_explorer_root)

        topbar_layout.addStretch()
        topbar_layout.addWidget(root_btn)

        explorer_layout.addWidget(topbar)

        # Tab widget for settings categories
        file_view = self.init_explorer()

        explorer_layout.addWidget(file_view)

        self.content_stack.addWidget(explorer_container)

    def show_content(self, index, button):
        # Update content stack to show the selected content
        self.content_stack.setCurrentIndex(index)

        # Generate content based on selected tab
        match button.objectName():
            case "dashboard_btn":
                print("Dashboard")
            case "results_btn":
                gui_support.load_html_content(self.results_viewer, "results/results.html", self.root_dir)
            case "professors_btn":
                gui_support.load_html_content(self.professor_view_viewer, "results/professors_data.html", self.root_dir)
            case "subjects_btn":
                gui_support.load_html_content(self.subject_view_viewer, "results/subjects_data.html", self.root_dir)
            case "explorer_btn":
                print("Explorer")
                # self.load_html_content(self.explorer_viewer, "results/explorer.html", self.root_dir)

        # Reset all sidebar button styles
        for btn_name in ["dashboard_btn", "results_btn", "professors_btn", "subjects_btn", "explorer_btn"]:
            btn = self.sidebar.findChild(QPushButton, btn_name)
            btn.setStyleSheet(
                "QPushButton { background-color: #2c3e50; color: white; text-align: left; padding: 10px; border: none; }"
            )

        # Set selected button style
        button.setStyleSheet(
            "QPushButton { background-color: #3a7ebf; color: white; text-align: left; padding: 10px; border: none; }"
        )

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
        self.load_documentation_tree(self.tree_viewer)
        self.running_spinner.stop()

    def generate_documentation_tree(self, parent_widget):
        """
        Generates the documentation tree, in a separate thread.
        """
        self.running_spinner = WaitingSpinner(parent_widget, True, True, Qt.ApplicationModal)
        self.running_spinner.start()
        parent_widget.setHtml(f"<h2>Generating documentation tree...</h2><p>Please wait...</p>")
        self.thread = QtCore.QThread()
        self.worker = Worker(root_dir=self.root_dir)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.generated_tree.connect(self.thread.quit)
        self.worker.generated_tree.connect(self.load_gen_tree)
        self.thread.start()

    def load_documentation_tree(self, parent_widget):
        """
        Loads the documentation tree.
        """
        documentation_structure = self.gen_tree
        if documentation_structure != '':
            parent_widget.setHtml(f"<h2>Documentation structure</h2><pre>{documentation_structure}</pre>")
        elif not os.path.exists(os.path.join(self.root_dir, Path('tmp/input_files'))):
            documentation_structure = "Documentation tree could not be generated - no input files found."
            parent_widget.setHtml(f"<h2>Documentation structure</h2><p>{documentation_structure}</p>")
        else:
            self.generate_documentation_tree(parent_widget)

    def open_link(self, link):
        """
        Opens data represented by the given link in a new window.

        Args:
            link (str):     Link to the data.
        Returns:
            None
        """
        try:
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
                self.new_window = TableWindow(dir_name=os.path.dirname(__file__), table_html=subj_html)
                self.new_window.setWindowTitle(f"Professor: {item['name']}")
                self.new_window.show()
                break
        except Exception as e:
            print(f'Error loading file:\n    {e}')
            load_dialog = gui_support.PopupDialog("Error loading data", f"Error loading data. Table data could not be loaded.", self)
            load_dialog.setModal(True)
            load_dialog.exec_()
            return

    def init_explorer(self):
        self.model = QFileSystemModel()
        self.model.setRootPath(os.path.expanduser("~"))
        self.file_view = QTreeView()
        self.file_view.setModel(self.model)
        if not os.path.exists(os.path.join(os.getcwd(), Path('tmp/input_files'))):
            self.file_view.setRootIndex(self.model.index(os.path.expanduser("~")))
        else:
            self.file_view.setRootIndex(self.model.index(os.path.join(os.getcwd(), Path('tmp/input_files'))))
        self.file_view.doubleClicked.connect(self.open_item)
        return self.file_view

    def set_explorer_root(self):
        root_dir = QFileDialog.getExistingDirectory(self, "Select Folder", os.path.expanduser("~"))
        if root_dir:
            self.file_view.setRootIndex(self.model.index(root_dir))

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
        else:
            # os.startfile(path)  # Opens file with default application
            if sys.platform.startswith('win'):
                os.startfile(path)
            else:
                opener = "open" if sys.platform == "darwin" else "xdg-open"
                subprocess.call([opener, path])

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
        icon.addPixmap(QtGui.QPixmap(os.path.join(dir_name if dir_name != '' else os.path.dirname(__file__), Path("resources/raf_logo_win.png"))), QtGui.QIcon.Normal, QtGui.QIcon.On)
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
    sys.exit(app.exec_())