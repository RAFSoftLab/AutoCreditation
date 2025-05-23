"""
GUI application for AutoCreditation
"""
import json
import os
from pathlib import Path
import shutil
import sys
from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import QPixmap, QFont
import PyQt5.QtGui as QtGui
from PyQt5.QtWidgets import (QApplication, QMainWindow, QSystemTrayIcon, QPushButton, QDesktopWidget,
                             QLineEdit, QTextEdit, QWidget, QLabel, QCheckBox, QGridLayout, QVBoxLayout,
                             QHBoxLayout, QProgressBar, QStackedWidget, QFrame, QTabWidget, QFileDialog,
                             QSizePolicy)
from pyqtspinner.spinner import WaitingSpinner

import src.util as util
import src.gui.main_worker as main_worker
import src.gui.gui_explorer as gui_explorer
import src.gui.gui_support as gui_support
import src.db_support as db_support
import src.verify_data as verify_data

dirName = os.path.dirname(__file__)

if sys.platform.startswith('win'):
    import ctypes
    myappid = 'mycompany.myproduct.subproduct.version' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

class MainWindow(QMainWindow):
    """
    Main window of the GUI application
    """

    def __init__(self, root_dir):
        super(MainWindow, self).__init__()
        doc_dir = ''
        root_dir = root_dir
        print(f"Application root directory: {root_dir}")
        # util.install_office_package() Package moced to requirements.txt as conditional
        self.setWindowTitle("AutoCreditation")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(os.path.join(dirName, Path("resources/raf_logo_win.png"))), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.setWindowIcon(icon)
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setIcon(icon)
        self.setMinimumSize(1000, 600)

        self.root_dir = root_dir
        self.doc_dir = doc_dir if doc_dir else os.path.expanduser("~")
        self.valid_doc_dir = False
        self.clean_tmp = True
        self.copy_files = True
        self.finished = False
        self.output_text = ''
        self.errors = []
        self.doc_map = {}

        # Processing options: list of tests to run
        # Initial values
        self.processing_options = {
            'use_loaded_data': True,
            'prof_subj_comp': True,
            'prof_subj_min_num': 2,
            'exam_points_sum': True
        }

        # Initialize the UI
        self.init_ui()

    def init_ui(self):
        # Main central widget and layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        self.setCentralWidget(central_widget)

        # Create top panel
        self.top_panel = self.create_top_panel()
        main_layout.addWidget(self.top_panel)

        # Create content area (stacked widget to switch between different content)
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack)

        # Set stretch factor to make content area use more space
        main_layout.setStretchFactor(self.top_panel, 0)
        main_layout.setStretchFactor(self.content_stack, 4)

        # Create content widgets
        self.create_results_widget()
        self.create_options_widget()

        # Set default to Results
        self.content_stack.setCurrentIndex(0)
        # self.showMaximized()

    def create_top_panel(self):
        # Create top panel frame
        top_panel = QFrame()
        top_panel.setObjectName("top_panel")
        top_panel.setStyleSheet("""
            #top_panel {
                background-color: #f0f0f0;
                border-bottom: 1px solid #ddd;
                min-height: 150px;
            }
            QPushButton {
                background-color: #2c3e50;
                color: white;
                padding: 5px 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
                color: #ecf0f1;
            }
        """)

        # Create panel layout
        panel_layout = QGridLayout(top_panel)

        # Documentation directory controls
        self.doc_dir_label = QLabel("Documentation directory:")
        self.doc_dir_label.setFont(QFont("Arial", 10))
        panel_layout.addWidget(self.doc_dir_label, 0, 0, 1, 3, alignment=Qt.AlignmentFlag.AlignBottom)

        self.doc_dir_text_line = QLineEdit()
        self.doc_dir_text_line.setToolTip("Path to the folder where the documentation files are located.")
        self.doc_dir_text_line.setText(self.doc_dir)
        self.doc_dir_text_line.setMinimumWidth(self.doc_dir_text_line.fontMetrics().averageCharWidth() * 80)
        self.doc_dir_text_line.textChanged.connect(self.update_doc_dir)
        self.doc_dir_text_line.textChanged.connect(self.update_valid_doc_dir)
        panel_layout.addWidget(self.doc_dir_text_line, 1, 0, 1, 3)

        self.choose_doc_dir_button = QPushButton("Choose directory")
        self.choose_doc_dir_button.setIcon(gui_support.create_icon('folder'))
        self.choose_doc_dir_button.setToolTip("Choose the folder where the documentation files are located.")
        self.choose_doc_dir_button.setMinimumWidth(150)
        self.choose_doc_dir_button.clicked.connect(self.choose_doc_dir)
        panel_layout.addWidget(self.choose_doc_dir_button, 1, 3, 1, 1)

        # Valid directory check label
        self.valid_doc_dir_label = QLabel()
        self.update_valid_doc_dir()
        panel_layout.addWidget(self.valid_doc_dir_label, 2, 0, 1, 3)

        # Action buttons
        self.run_button = QPushButton("Run")
        self.run_button.setIcon(gui_support.create_icon('check'))
        self.run_button.setToolTip("Run the application.")
        self.run_button.setMinimumWidth(150)
        self.set_run_button_enabled(False)
        self.run_button.clicked.connect(self.run)
        panel_layout.addWidget(self.run_button, 2, 3, 1, 1)

        self.options_button = QPushButton("Options")
        self.options_button.setIcon(gui_support.create_icon('cog'))
        self.options_button.setToolTip("Processing progress output / Options for the application.")
        self.options_button.setMinimumWidth(150)
        self.options_button.clicked.connect(self.toggle_options_click)
        panel_layout.addWidget(self.options_button, 1, 4, 1, 1)

        self.results_button = QPushButton("Results Explorer")
        self.results_button.setIcon(gui_support.create_icon('database'))
        self.results_button.setToolTip("Open results and documentation explorer.")
        self.results_button.setMinimumWidth(150)
        self.results_button.setEnabled(self.finished or (os.path.exists(os.path.join(self.root_dir, Path('tmp/results/results.json')))))
        self.results_button.clicked.connect(self.load_results)
        panel_layout.addWidget(self.results_button, 2, 4, 1, 1)

        # Logo
        self.logo_label = QLabel()
        self.logo_label.setPixmap(QtGui.QPixmap(os.path.join(dirName, Path("resources/raf_logo_no_bg.png"))).scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.logo_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        panel_layout.addWidget(self.logo_label, 0, 4, 1, 1, Qt.AlignCenter)

        return top_panel

    def create_results_widget(self):
        # Results container with content area
        results_container = QWidget()
        results_layout = QVBoxLayout(results_container)
        results_layout.setContentsMargins(0, 0, 0, 0)

        # Top bar for Results
        topbar = QFrame()
        # topbar.setStyleSheet("background-color: #f0f0f0; border-bottom: 1px solid #ddd;")
        topbar_layout = QHBoxLayout(topbar)

        # Create a stacked widget to toggle between results label and progress indicators
        self.results_header_stack = QStackedWidget()

        # First page - regular label
        label_widget = QWidget()
        label_layout = QHBoxLayout(label_widget)
        label_layout.setContentsMargins(0, 0, 0, 0)

        self.results_label = QLabel("Documentation Processing")
        self.results_label.setFont(QFont("Arial", 14, QFont.Bold))
        label_layout.addWidget(self.results_label)
        # label_layout.addStretch()

        # Second page - progress indicators
        progress_widget = QWidget()
        progress_layout = QHBoxLayout(progress_widget)
        progress_layout.setContentsMargins(0, 0, 0, 0)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        progress_layout.addWidget(self.progress_bar, stretch=1)

        self.progress_desc_label = QLabel()
        self.progress_desc_label.setFixedHeight(20)
        self.progress_desc_label.setText('')
        progress_layout.addWidget(self.progress_desc_label, stretch=1)

        # Add both pages to stacked widget
        self.results_header_stack.addWidget(label_widget)
        self.results_header_stack.addWidget(progress_widget)

        # Add stacked widget to topbar
        topbar_layout.addWidget(self.results_header_stack)
        # topbar_layout.addStretch()

        results_layout.addWidget(topbar)

        # Results text area
        self.results_text_area = QTextEdit()
        self.results_text_area.setReadOnly(True)
        self.results_text_area.setMinimumHeight(self.results_text_area.fontMetrics().height() * 30)
        self.results_text_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.results_text_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Running spinner
        self.running_spinner = WaitingSpinner(self.results_text_area, True, True, Qt.ApplicationModal)

        results_layout.addWidget(self.results_text_area)

        self.content_stack.addWidget(results_container)


    def create_options_widget(self):
        # Options container with content area
        options_container = QWidget()
        options_layout = QVBoxLayout(options_container)
        options_layout.setContentsMargins(0, 0, 0, 0)

        # Top bar for Options
        topbar = QFrame()
        # topbar.setStyleSheet("background-color: #f0f0f0; border-bottom: 1px solid #ddd;")
        topbar_layout = QHBoxLayout(topbar)

        options_label = QLabel("Application Options")
        options_label.setFont(QFont("Arial", 14, QFont.Bold))
        topbar_layout.addWidget(options_label)
        topbar_layout.addStretch()

        options_layout.addWidget(topbar)

        # Tab widget for options
        self.options_tab_widget = QTabWidget()
        self.options_tab_widget.setStyleSheet("""
                QPushButton {
                background-color: #2c3e50;
                color: white;
                padding: 5px 10px;
                border: none;
            }
            """
        )

        # General options tab
        general_options_tab = QWidget()
        general_layout = QVBoxLayout(general_options_tab)
        general_layout.setContentsMargins(20, 20, 20, 20)
        general_layout.setSpacing(15)

        save_export_layout = QHBoxLayout()

        self.save_results_button = QPushButton("Save Results")
        self.save_results_button.setIcon(gui_support.create_icon('exclamation'))
        self.save_results_button.setToolTip("Save results to a .json file.")
        self.save_results_button.setMinimumWidth(200)
        self.save_results_button.clicked.connect(self.save_data)
        save_export_layout.addWidget(self.save_results_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.import_databese_button = QPushButton("Export Database")
        self.import_databese_button.setIcon(gui_support.create_icon('database'))
        self.import_databese_button.setToolTip("Import database from a .db file.")
        self.import_databese_button.setMinimumWidth(200)
        self.import_databese_button.clicked.connect(self.export_database)
        save_export_layout.addWidget(self.import_databese_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        general_layout.addLayout(save_export_layout)

        load_import_layout = QHBoxLayout()

        self.load_results_button = QPushButton("Load Results")
        self.load_results_button.setIcon(gui_support.create_icon('floppy'))
        self.load_results_button.setToolTip("Load results from previous run.")
        self.load_results_button.setMinimumWidth(200)
        self.load_results_button.clicked.connect(self.load_data)
        load_import_layout.addWidget(self.load_results_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.import_databese_button = QPushButton("Import Database")
        self.import_databese_button.setIcon(gui_support.create_icon('database'))
        self.import_databese_button.setToolTip("Import database from a .db file.")
        self.import_databese_button.setMinimumWidth(200)
        self.import_databese_button.clicked.connect(self.import_database)
        load_import_layout.addWidget(self.import_databese_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        general_layout.addLayout(load_import_layout)

        self.clean_tmp_checkbox = QCheckBox('Clean /tmp directory')
        self.clean_tmp_checkbox.setChecked(True)
        self.clean_tmp_checkbox.setToolTip("Empty the /tmp directory before running the application.")
        self.clean_tmp_checkbox.setMinimumWidth(200)
        self.clean_tmp_checkbox.clicked.connect(self.update_clean_tmp)
        general_layout.addWidget(self.clean_tmp_checkbox)

        self.use_loaded_data = QCheckBox('Use extracted documentation data if found')
        self.use_loaded_data.setChecked(True)
        self.use_loaded_data.setToolTip("If checked and extracted doucumentation is found (is loaded) uses it. Otherwise, copies documentation files and extracts data before processing and testing.")
        general_layout.addWidget(self.use_loaded_data)

        general_layout.addStretch()

        # Test options tab
        test_options_tab = QWidget()
        test_layout = QVBoxLayout(test_options_tab)
        test_layout.setContentsMargins(20, 20, 20, 20)
        test_layout.setSpacing(15)

        # Add test option controls
        test_params_label = QLabel("Processing Parameters")
        test_params_label.setFont(QFont("Arial", 12, QFont.Bold))
        test_layout.addWidget(test_params_label)

        # Parameter Group 1
        self.prof_subj_comp = QCheckBox("Professor-subjects comparison")
        self.prof_subj_comp.setToolTip("Compare subjects listed in professors file with subjects listed in subjects file and vice versa.")
        self.prof_subj_comp.setChecked(True)
        self.prof_subj_comp.setDisabled(True)
        test_layout.addWidget(self.prof_subj_comp)

        subj_num = QWidget()
        subj_layout = QGridLayout(subj_num)
        subj_layout.setContentsMargins(0, 0, 0, 0)
        self.prof_subj_min_num_checkbox = QCheckBox("Minimum number of subjects per professor")
        self.prof_subj_min_num_checkbox.setToolTip("Verify professors have at least this number of subjects.")
        self.prof_subj_min_num_checkbox.setChecked(True)
        self.prof_subj_min_num_checkbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.prof_subj_min_num_checkbox.setFixedHeight(20)
        subj_layout.addWidget(self.prof_subj_min_num_checkbox, 0, 0, 1, 1, alignment=Qt.AlignmentFlag.AlignLeft)
        self.prof_subj_min_num = QLineEdit()
        self.prof_subj_min_num.setFixedWidth(50)
        self.prof_subj_min_num.setFixedHeight(20)
        self.prof_subj_min_num.setText("2")
        subj_layout.addWidget(self.prof_subj_min_num, 0, 1, 1, 2, alignment=Qt.AlignmentFlag.AlignLeft)
        self.prof_subj_min_num_checkbox.stateChanged.connect(self.prof_subj_min_num.setVisible)
        test_layout.addWidget(subj_num)

        self.exam_points_sum = QCheckBox("Exam points sum verification")
        self.exam_points_sum.setToolTip("Verify that the sum of all exam points is equal to the total number of points for that subject.")
        self.exam_points_sum.setChecked(True)
        test_layout.addWidget(self.exam_points_sum)

        # Parameter Group 2
        # test_params_label2 = QLabel("Document Analysis")
        # test_params_label2.setFont(QFont("Arial", 12, QFont.Bold))
        # test_layout.addWidget(test_params_label2, alignment=Qt.AlignmentFlag.AlignLeft)
        # test_layout.addSpacing(5)

        # self.test_param3_checkbox = QCheckBox("Extract metadata")
        # self.test_param3_checkbox.setChecked(True)
        # test_layout.addWidget(self.test_param3_checkbox)

        # self.test_param4_checkbox = QCheckBox("Perform deep analysis")
        # self.test_param4_checkbox.setChecked(True)
        # test_layout.addWidget(self.test_param4_checkbox)

        # self.test_param5_checkbox = QCheckBox("Generate detailed reports")
        # self.test_param5_checkbox.setChecked(True)
        # test_layout.addWidget(self.test_param5_checkbox)

        test_layout.addStretch()

        # Add tabs to the options tab widget
        self.options_tab_widget.addTab(general_options_tab, "General")
        self.options_tab_widget.addTab(test_options_tab, "Test Options")

        options_layout.addWidget(self.options_tab_widget)

        self.content_stack.addWidget(options_container)

    def update_doc_dir_text_line(self, new_text):
        """
        Fill the documentation directory path text line with the new_text.
        """
        self.doc_dir_text_line.setText(new_text)

    def update_doc_dir(self):
        """
        Update the documentation directory path with path from the text line.
        """
        self.doc_dir = self.doc_dir_text_line.text()

    def choose_doc_dir(self):
        """
        Open a file dialog to choose a documentation directory.
        """
        doc_dir = QtWidgets.QFileDialog.getExistingDirectory(self, "Select folder", os.path.expanduser("~"))
        if doc_dir != '':
            self.update_doc_dir_text_line(doc_dir)

    def update_valid_doc_dir(self):
        """
        Check if the documentation directory is valid, and update the valid_doc_dir_label accordingly.
        """
        self.valid_doc_dir = True if self.doc_dir not in ['', os.path.expanduser("~")] and os.path.isdir(self.doc_dir) else False
        if self.doc_dir == '':
            self.valid_doc_dir_label.setText("No documentation directory selected. Please select one.")
            self.valid_doc_dir_label.setStyleSheet("color: red;")
            self.set_run_button_enabled(False)
        elif self.valid_doc_dir == True:
            self.valid_doc_dir_label.setText("Valid directory path.")
            self.valid_doc_dir_label.setStyleSheet("color: green;")
            self.set_run_button_enabled(True)
        else:
            self.valid_doc_dir_label.setText("Invalid directory path.")
            self.valid_doc_dir_label.setStyleSheet("color: red;")
            self.set_run_button_enabled(False)
        self.valid_doc_dir_label.adjustSize()

    def update_processing_options(self, option, value):
        """
        Update the processing options list based on checkboxes and text boxes.
        """
        self.processing_options[option] = value

    def toggle_options_click(self):
        """
        Switch between options view and results view
        """
        current_index = self.content_stack.currentIndex()
        self.content_stack.setCurrentIndex(1 if current_index == 0 else 0)
        self.options_button.setText("Results" if current_index == 0 else "Options")

    def load_results(self):
        """
        Load results from previous run if available, display popup if not
        """
        if util.check_files_exist(root_dir=self.root_dir) == False:
            popup_message = gui_support.PopupDialog("No results data found. Please run the application first.", 'Data not found', self)
            popup_message.setModal(True)
            popup_message.exec_()
            return
        self.generate_results_html_open_explorer()

    def set_run_button_enabled(self, enabled):
        """
        Enable or disable the run button.
        """
        if not hasattr(self, 'run_button'):
            return
        self.run_button.setEnabled(enabled)

    def update_clean_tmp(self):
        """
        Update clean_tmp flag based on checkbox.
        """
        self.clean_tmp = self.clean_tmp_checkbox.isChecked()

    @pyqtSlot(bool)
    def setProgressBarVisible(self, visible):
        """
        Set the progress bar visibility to value of visible.

        Args:
            visible (bool):     True if the progress bar should be visible, False otherwise.
        Returns:
            None.
        """
        self.content_stack.setCurrentIndex(0)  # Show results view
        self.options_button.setText("Options")

        # Switch between results label and progress indicators in the stacked widget
        if visible:
            self.results_header_stack.setCurrentIndex(1)  # Show progress indicators
        else:
            self.results_header_stack.setCurrentIndex(0)  # Show results label

    @pyqtSlot(int, str)
    def setProgressBarValue(self, value, desc=''):
        """
        Set the progress bar value to passed value.

        Args:
            value (int):        Value of the progress bar.
            desc (str):         Description text for the progress.
        Returns:
            None.
        """
        self.progress_bar.setValue(value)
        if desc != '':
            self.progress_bar.setStatusTip(desc)
            self.progress_desc_label.setText(desc)
            self.progress_desc_label.adjustSize()


    @QtCore.pyqtSlot(dict)
    def update_results(self, results):
        """
        Update the results text area with the results.
        """
        if type(results) == str:
            self.output_text += results
            self.results_text_area.setText(self.output_text)
        elif type(results) == dict:
            for key in results:
                if type(results[key]) == str:
                    self.output_text += '\n- - - {}: \n{}\n- - -\n'.format(key, results[key])
                    continue
                if type(results[key]) == dict:
                    self.output_text += '\n- - - {}: \n{}\n- - -\n'.format(key, json.dumps(results[key], indent=4, ensure_ascii=False))
                    continue
                if type(results[key]) == list:
                    items_list = []
                    for item in results[key]:
                        if type(item) == str:
                            items_list.append(item)
                        elif type(item) == dict:
                            items_list.append(json.dumps(item, indent=4, ensure_ascii=False))
                        elif type(item) == list:
                            items_list.append('\n'.join(item))
                        else:
                            items_list.append(str(item))
                    self.output_text += '\n- - - {}: \n{}\n- - -\n'.format(key, '\n'.join(items_list))
                    continue
                self.output_text += '\n{}'.format(str(results[key]))
            self.results_text_area.setText(self.output_text)
        elif type(results) == list:
            self.results_text_area.setText('\n'.join(results))
        else:
            self.results_text_area.setText(str(results))
        self.scroll_to_bottom()

    def scroll_to_bottom(self):
        """
        Scroll to bottom of the text area.
        """
        self.results_text_area.verticalScrollBar().setValue(self.results_text_area.verticalScrollBar().maximum())

    @QtCore.pyqtSlot(list)
    def update_errors(self, errors):
        """
        Update list of errors.
        """
        self.errors += errors

    @QtCore.pyqtSlot(dict)
    def update_doc_map(self, doc_map):
        """
        Update the document map.
        """
        for item_key in doc_map.keys():
            if item_key not in self.doc_map.keys():
                self.doc_map[item_key] = doc_map[item_key]
            else:
                self.doc_map[item_key] = doc_map[item_key]

    def lock_gui(self, lock=True):
        """
        Lock the GUI elements of the main window.
        """
        self.doc_dir_text_line.setEnabled(not lock)
        self.choose_doc_dir_button.setEnabled(not lock)
        self.run_button.setEnabled(not lock)
        self.options_button.setEnabled(not lock)
        self.results_button.setEnabled(not lock)
        if lock == True:
            self.run_button.setText("Running...")
        else:
            self.run_button.setText("Run")

    def open_explorer(self):
        """
        Open results and file explorer to the results directory.
        """
        self.explorer = gui_explorer.FileExplorer(root_dir=self.root_dir)
        self.explorer.setWindowModality(Qt.ApplicationModal)
        self.explorer.show()

    def generate_results_html_open_explorer(self):
        """
        Generates results HTML file and opens explorer
        """
        gui_support.generate_html(self.root_dir, params={'check_subj_points_sum': self.processing_options['exam_points_sum'], 'min_subj_per_prof': self.processing_options['prof_subj_min_num']})
        gui_support.generate_prof_html(self.root_dir)
        gui_support.generate_subjects_html(self.root_dir)
        self.open_explorer()

    def save_data(self):
        """
        Saves results to a .json file.
        """
        if util.check_files_exist(root_dir=self.root_dir) == False:
            popup_message = gui_support.PopupDialog("No results data found. Please run the application first.", 'Data not found', self)
            popup_message.setModal(True)
            popup_message.exec_()
            return
        try:
            self.results = util.load_data(root_dir=self.root_dir, abs_path=os.path.join(self.root_dir, Path('tmp/results/results.json')))
            self.prof_data = util.load_data(root_dir=self.root_dir, abs_path=os.path.join(self.root_dir, Path('tmp/professors_data.json')))
            self.subj_data = util.load_data(root_dir=self.root_dir, abs_path=os.path.join(self.root_dir, Path('tmp/subjects_data.json')))
        except Exception as e:
            print(f'Error loading data:\n    {e}')
            return
        file_path = QFileDialog.getSaveFileName(self, "Save data", os.path.expanduser("~"), filter="*.json")
        file_path = file_path[0] if type(file_path) in [tuple, list] and file_path[0] != '' else file_path if type(file_path) == str else ''
        if not file_path.endswith('.json') and not os.path.exists(file_path) and file_path != '':
            file_path = os.path.join(os.path.dirname(file_path), '.json')
        if not file_path.endswith('.json') and not file_path == '':
            file_path = ''
            error_dialog = gui_support.PopupDialog("File must be a .json file.", "Invalid file selected.", self)
            error_dialog.setModal(True)
            error_dialog.exec_()
        if file_path != '':
            res_data = {'results': self.results, 'professors': self.prof_data, 'subjects': self.subj_data}
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            util.save_json(file_path=file_path, data=res_data)
            saved_dialog = gui_support.PopupDialog(f"Results saved to {file_path}.", "Results saved", self)
            saved_dialog.setModal(True)
            saved_dialog.exec_()

    def load_data(self):
        """
        Opens file explorer to choose a file to load.
        """
        file_path = QFileDialog.getOpenFileName(self, "Load data", os.path.expanduser("~"))
        file_path = file_path[0] if type(file_path) in [tuple, list] and file_path[0] != '' else file_path if type(file_path) == str else ''
        if not file_path.endswith('.json') and not file_path == '':
            file_path = ''
            error_dialog = gui_support.PopupDialog("File must be a .json file.", "Invalid file selected.", self)
            error_dialog.setModal(True)
            error_dialog.exec_()
        if file_path != '':
            os.makedirs(os.path.join(self.root_dir, Path('tmp/results')), exist_ok=True)
            all_data = util.load_json(file_path=file_path)
            if 'results' not in all_data.keys():
                error_dialog = gui_support.PopupDialog("Save file is invalid: data format unsupported.", "Invalid file selected.", self)
                error_dialog.setModal(True)
                error_dialog.exec_()
                return
            util.save_data(root_dir=self.root_dir, data=all_data['results'], save_dir='tmp/results', data_name='results')
            util.save_data(root_dir=self.root_dir, data=all_data['professors'], save_dir='tmp', data_name='professors_data')
            util.save_data(root_dir=self.root_dir, data=all_data['subjects'], save_dir='tmp', data_name='subjects_data')
            db_support.json_to_db(os.path.join(self.root_dir, Path('tmp/professors_data.json')),
                                  os.path.join(self.root_dir, Path('tmp/subjects_data.json')),
                                  os.path.join(self.root_dir, Path('tmp/results/results.json')),
                                  os.path.join(self.root_dir, Path('tmp/acreditation.db')))
            self.results_button.setEnabled(True)
            loaded_dialog = gui_support.PopupDialog(f"Data from {file_path} loaded.", "Data loaded", self)
            loaded_dialog.setModal(True)
            loaded_dialog.exec_()
            self.run_button.setEnabled(True)

    def import_database(self):
        """
        Import database from a .db file.
        """
        file_path = QFileDialog.getOpenFileName(self, "Import database", os.path.expanduser("~"))
        file_path = file_path[0] if type(file_path) in [tuple, list] and file_path[0] != '' else file_path if type(file_path) == str else ''
        if not file_path.endswith('.db') and not os.path.exists(file_path) and file_path != '':
            file_path = ''
            error_dialog = gui_support.PopupDialog("File must be a .db file.", "Invalid file selected.", self)
            error_dialog.setModal(True)
            error_dialog.exec_()
        if file_path != '':
            os.makedirs(os.path.join(self.root_dir, Path('tmp')), exist_ok=True)
            shutil.copyfile(file_path, os.path.join(self.root_dir, Path('tmp/acreditation.db')))
            db_support.db_to_json(os.path.join(self.root_dir, Path('tmp/acreditation.db')),
                                  os.path.join(self.root_dir, Path('tmp/professors_data.json')),
                                  os.path.join(self.root_dir, Path('tmp/subjects_data.json')),
                                  os.path.join(self.root_dir, Path('tmp/results/results.json')))
            self.results_button.setEnabled(True)
            loaded_dialog = gui_support.PopupDialog(f"Database from {file_path} imported.", "Database imported", self)
            loaded_dialog.setModal(True)
            loaded_dialog.exec_()
            self.run_button.setEnabled(True)

    def export_database(self):
        """
        Export database to a .db file.
        """
        file_path = QFileDialog.getSaveFileName(self, "Export database", os.path.expanduser("~"), filter="*.db")
        file_path = file_path[0] if type(file_path) in [tuple, list] and file_path[0] != '' else file_path if type(file_path) == str else ''
        if not file_path.endswith('.db') and not os.path.exists(file_path) and file_path != '':
            file_path = ''
            error_dialog = gui_support.PopupDialog("File must be a .db file.", "Invalid file selected.", self)
            error_dialog.setModal(True)
            error_dialog.exec_()
        if file_path != '':
            shutil.copyfile(os.path.join(self.root_dir, Path('tmp/acreditation.db')), file_path)
            saved_dialog = gui_support.PopupDialog(f"Database exported to {file_path}.", "Database exported", self)
            saved_dialog.setModal(True)
            saved_dialog.exec_()

    @QtCore.pyqtSlot(dict)
    def finished_run(self):
        """
        Called when the run is finished.
        """
        self.lock_gui(lock=False)
        self.running_spinner.stop()
        self.finished = True
        self.choose_doc_dir_button.setEnabled(True)
        self.set_run_button_enabled(True)
        self.options_button.setEnabled(True)
        self.results_button.setEnabled(True)
        self.scroll_to_bottom()

        # Switch back to showing the results label
        self.results_header_stack.setCurrentIndex(0)

        self.generate_results_html_open_explorer()


    def run(self):
        """
        Run the main application.
        """
        print("Running application...")
        self.lock_gui()
        self.running_spinner.start()

        self.update_processing_options('use_loaded_data', self.use_loaded_data.isChecked())
        if self.prof_subj_min_num.text().isdecimal() == True:
            self.update_processing_options('prof_subj_min_num', int(self.prof_subj_min_num.text()))
        self.update_processing_options('prof_subj_comp', self.prof_subj_comp.isChecked())
        self.update_processing_options('exam_points_sum', self.exam_points_sum.isChecked())

        self.thread = QThread()
        self.worker = main_worker.Worker()
        self.worker.setInput(root_dir=self.root_dir, doc_dir=self.doc_dir, clean_tmp=self.clean_tmp, copy_files=self.copy_files, processing_options=self.processing_options)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress_bar_visibility.connect(self.setProgressBarVisible)
        self.worker.progress_bar_value.connect(self.setProgressBarValue)
        self.worker.updated_results.connect(self.update_results)
        self.worker.update_errors.connect(self.update_errors)
        self.worker.update_doc_map.connect(self.update_doc_map)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.finished_run)
        self.thread.start()


def window(root_dir):
    app = QApplication(sys.argv)
    win = MainWindow(root_dir=root_dir)
    win.show()
    # Center the window
    wPos = win.frameGeometry()
    cp = QDesktopWidget().availableGeometry().center()
    wPos.moveCenter(cp)
    win.move(wPos.topLeft())
    sys.exit(app.exec_())
