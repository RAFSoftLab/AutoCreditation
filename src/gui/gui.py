"""
GUI application for AutoCreditation
"""


import json
import os
from pathlib import Path
import sys
from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import QPixmap, QFont
import PyQt5.QtGui as QtGui
from PyQt5.QtWidgets import (QApplication, QMainWindow, QSystemTrayIcon, QPushButton, QDesktopWidget,
                             QLineEdit, QTextEdit, QWidget, QLabel, QCheckBox, QGridLayout, QVBoxLayout,
                             QProgressBar, QStackedWidget, QFrame, QTabWidget)
# TODO Remove after debugging:
# import debugpy
from pyqtspinner.spinner import WaitingSpinner

import src.util as util

import src.gui.main_worker as main_worker
import src.gui.gui_explorer as gui_explorer
import src.gui.gui_support as gui_support

dirName = os.path.dirname(__file__)

class MainWindow(QMainWindow):
    """
    Main window of the GUI application
    """


    def __init__(self, root_dir):
        super(MainWindow, self).__init__()
        doc_dir = ''
        root_dir = root_dir
        print(f"Application root directory: {root_dir}")
        util.install_office_package()
        self.initUI(root_dir=root_dir, doc_dir=doc_dir)

    def initUI(self, root_dir='', doc_dir=''):
        """
        Initializes the GUI application
        """

        self.setWindowTitle("AutoCreditation")
        # self.setGeometry(100, 100, 800, 600)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(os.path.join(dirName, Path("resources/raf_logo_win.png"))), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.setWindowIcon(icon)
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setIcon(icon)

        self.root_dir = root_dir
        self.doc_dir = doc_dir
        self.doc_dir = os.path.expanduser("~")
        self.valid_doc_dir = False
        self.clean_tmp = True
        self.copy_files = True
        self.finished = False
        self.output_text = ''
        self.erorrs = []
        self.doc_map = {}

        # self.center()

        # # # - - - GUI elements - - - # # #

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout()
        self.control_panel = QGridLayout()
        self.progress_panel = QGridLayout()
        self.output_panel = QGridLayout()

        # # # - - - GUI elements - - - # # #

        self.doc_dir_label = QLabel(self)
        self.doc_dir_label.setText("Documentation directory:")
        self.doc_dir_label.move(10, 10)
        self.doc_dir_label.adjustSize()
        self.control_panel.addWidget(self.doc_dir_label, 0, 0, 1, 3, alignment=Qt.AlignmentFlag.AlignBottom)

        # Documentation directory path label
        self.doc_dir_text_line = QLineEdit(self)
        self.doc_dir_text_line.setToolTip("Path to the folder where the documentation files are located.")
        self.doc_dir_text_line.setText(self.doc_dir)
        # self.doc_dir_text_line.setFixedWidth(480)
        self.doc_dir_text_line.setMinimumWidth(self.doc_dir_text_line.fontMetrics().averageCharWidth() * 100)
        self.doc_dir_text_line.move(10, 30)
        self.doc_dir_text_line.setToolTip("Select the folder where the documentation files are located.")
        self.doc_dir_text_line.textChanged.connect(self.update_doc_dir)
        self.doc_dir_text_line.textChanged.connect(self.update_valid_doc_dir)
        self.control_panel.addWidget(self.doc_dir_text_line, 1, 0, 1, 3)

        # Documentation directory selection button
        self.choose_doc_dir_button = QPushButton(self)
        self.choose_doc_dir_button.setText("Choose directory")
        self.choose_doc_dir_button.setToolTip("Choose the folder where the documentation files are located.")
        self.choose_doc_dir_button.move(500, 30)
        # self.choose_doc_dir_button.setFixedWidth(150)
        self.choose_doc_dir_button.setMinimumWidth(150)
        self.choose_doc_dir_button.clicked.connect(self.choose_doc_dir)
        self.control_panel.addWidget(self.choose_doc_dir_button, 1, 3, 1, 1)

        # Run button
        self.run_button = QPushButton(self)
        self.run_button.setText("Run")
        self.run_button.setToolTip("Run the application.")
        self.run_button.move(500, 60)
        # self.run_button.setFixedWidth(150)
        self.run_button.setMinimumWidth(150)
        self.set_run_button_enabled(False)
        self.run_button.clicked.connect(self.run)
        self.control_panel.addWidget(self.run_button, 2, 3, 1, 1)

        # Results button
        self.results_button = QPushButton(self)
        self.results_button.setText("Results")
        self.results_button.setToolTip("Open results in explorer.")
        # self.results_button.move(660, 90)
        self.results_button.setMinimumWidth(150)
        self.results_button.setEnabled(self.finished)
        self.results_button.clicked.connect(self.open_explorer)
        self.control_panel.addWidget(self.results_button, 2, 4, 1, 2)

        # Valid directory check label
        self.valid_doc_dir_label = QLabel(self)
        self.update_valid_doc_dir()
        self.valid_doc_dir_label.move(10, 60)
        self.valid_doc_dir_label.adjustSize()
        self.control_panel.addWidget(self.valid_doc_dir_label, 2, 0, 1, 3, alignment=Qt.AlignmentFlag.AlignTop)

        # Options button
        self.options_button = QPushButton(self)
        self.options_button.setText("Options")
        self.options_button.setToolTip("Options for the application.")
        self.options_button.setMinimumWidth(150)
        self.options_button.clicked.connect(self.toggle_options_click)
        self.control_panel.addWidget(self.options_button, 1, 4, 1, 2)

        # Results and output text area
        self.results_text_area = QTextEdit(self)
        self.results_text_area.setReadOnly(True)
        # self.results_text_area.move(10, 130)
        # self.results_text_area.resize(980, 800)
        self.results_text_area.setMinimumHeight(self.results_text_area.fontMetrics().height() * 30)
        self.results_text_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.results_text_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # self.output_panel.addWidget(self.results_text_area, 0, 0)

        # Options panel
        self.options_widget = QTabWidget()
        self.options_panel_widget = QWidget()
        self.options_panel_layout = QVBoxLayout()
        self.options_panel_layout.setContentsMargins(10, 10, 10, 10)
        self.options_panel_layout.setSpacing(5)
        self.load_results_button = QPushButton("Load Results", clicked=self.load_results)
        self.load_results_button.setToolTip("Load results from previous run.")
        self.load_results_button.setMinimumWidth(150)
        self.options_panel_layout.addWidget(self.load_results_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.clean_tmp_checkbox = QCheckBox('Clean /tmp directory', checked=True, clicked=self.update_clean_tmp)
        self.clean_tmp_checkbox.setToolTip("Empty the /tmp directory before running the application.")
        self.clean_tmp_checkbox.setMinimumWidth(150)
        self.options_panel_layout.addWidget(self.clean_tmp_checkbox, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.options_panel_layout.addStretch()
        self.options_panel_widget.setLayout(self.options_panel_layout)
        self.options_widget.addTab(self.options_panel_widget, "Options")


        self.stack = QStackedWidget()
        self.stack.addWidget(self.results_text_area)
        self.stack.addWidget(self.options_widget)
        self.stack.setCurrentIndex(0)
        self.output_panel.addWidget(self.stack)

        # Running spinner
        self.running_spinner = WaitingSpinner(self.results_text_area, True, True, Qt.ApplicationModal)

        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximum(100)
        # self.progress_bar.setGeometry(QtCore.QRect(10, 100, 200, 20))
        self.progress_bar.setVisible(False)
        self.progress_panel.addWidget(self.progress_bar, 0, 0, 1, 2)

        # Progress description
        self.progress_desc_label = QLabel(self)
        self.progress_desc_label.setFixedHeight(20)
        self.progress_desc_label.setText('')
        # self.progress_desc_label.setAlignment(Qt.AlignCenter)
        self.progress_desc_label.move(230, 100)
        # self.progress_desc_label.adjustSize()
        self.progress_panel.addWidget(self.progress_desc_label, 0, 2, 1, 3)

        # Logo
        self.logo_label = QLabel(self)
        self.logo_label.setPixmap(QtGui.QPixmap(os.path.join(dirName, Path("resources/raf_logo_no_bg.png"))).scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.logo_label.adjustSize()
        self.logo_label.move(self.width() - 10 - self.logo_label.width(), self.results_text_area.y() - self.logo_label.height() - 5)
        self.logo_label.show()

        self.control_panel_area = QGridLayout()
        self.control_panel_area.addLayout(self.control_panel, 0, 0, alignment=Qt.AlignmentFlag.AlignTop)
        self.control_panel_area.addWidget(self.logo_label, 0, 1, alignment=Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTop)
        self.control_panel_area.addLayout(self.progress_panel, 1, 0)

        self.main_layout.addLayout(self.control_panel_area, stretch=0)
        self.main_layout.addLayout(self.output_panel, stretch=2)
        self.central_widget.setLayout(self.main_layout)

        # self.center()

    # # # - - - GUI functions - - - # # #

    def center(self):
        """
        Center the window on the screen.
        """
        wPos = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        wPos.moveCenter(cp)
        self.move(wPos.topLeft())

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

    def toggle_options(self, set_view='-1'):
        """
        Switch to options panel
        """
        view_map = {
            'progress' : 0,
            '0': 0,
            'options': 1,
            '1': 1,
            '-1': (1 - self.stack.currentIndex())
        }
        button_text_map = {
            '0': 'Options',
            '1': 'Show Progress'
        }

        self.stack.setCurrentIndex(view_map[set_view])
        self.options_button.setText(button_text_map[str(view_map[set_view])])

    def toggle_options_click(self):
        """
        Switch between options panel and progress panel on button click
        """
        self.toggle_options()

    def load_results(self):
        """
        Load results from previous run if available, display popup if not
        """
        results_json_path = os.path.join(self.root_dir, Path('tmp/results/results.json'))
        prof_json_path = os.path.join(self.root_dir, Path('tmp/professors_data.json'))
        subj_json_path = os.path.join(self.root_dir, Path('tmp/subjects_data.json'))
        if False in [True if os.path.exists(curr_path) else False for curr_path in [results_json_path, prof_json_path, subj_json_path]]:
            popup_message = gui_support.PopupDialog("No results data found. Please run the application first.", 'Data not found', self)
            popup_message.setModal(True)
            popup_message.exec_()
            return
        self.generate_results_html_open_explorer()

    def set_run_button_enabled(self, enabled):
        """
        Enable or disable the run button.
        """
        self.run_button.setEnabled(enabled)

    def update_clean_tmp(self):
        """
        Clean the /tmp directory.
        """
        self.clean_tmp = True if self.clean_tmp_checkbox.isChecked() else False

    @pyqtSlot(bool)
    def setProgressBarVisible(self, visible):
        """
        Set the progress bar visibility to value of visible.

        Args:
            visible (bool):     True if the progress bar should be visible, False otherwise.
        Returns:
            None.
        """
        self.toggle_options(set_view='progress')
        self.progress_bar.setVisible(visible)
        self.progress_desc_label.setVisible(visible)

    @pyqtSlot(int, str)
    def setProgressBarValue(self, value, desc=''):
        """
        Set the progress bar value to passed value.

        Args:
            value (int):        Value of the progress bar.
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

    # @QtCore.pyqtSlot()
    def lock_gui(self, lock=True):
        """
        Lock the GUI elements of the main window.
        """
        self.doc_dir_text_line.setEnabled(not lock)
        self.choose_doc_dir_button.setEnabled(not lock)
        self.run_button.setEnabled(not lock)
        self.options_button.setEnabled(not lock)
        if lock == True:
            self.run_button.setText("Running...")
        else:
            self.run_button.setText("Run")

    def generate_html(self, root_dir=''):
        """
        Generates HTML files from the results.
        """
        root_dir = root_dir if root_dir != '' else self.root_dir
        print("Generating HTML files...")
        try:
            util.generate_res_html(root_dir=root_dir)
        except Exception as e:
            print(f'Error generating HTML files:\n    {e}')

    def generate_prof_html(self, root_dir=''):
        """
        Generates professors data HTML file.
        """
        root_dir = root_dir if root_dir != '' else self.root_dir
        print("Generating professors data HTML file...")
        try:
            util.generate_prof_html(root_dir=root_dir)
        except Exception as e:
            print(f'Error generating professors data HTML file:\n    {e}')

    def generate_subjects_html(self, root_dir=''):
        """
        Generates subjects data HTML file.
        """
        root_dir = root_dir if root_dir != '' else self.root_dir
        print("Generating subjects data HTML file...")
        try:
            util.generate_subjects_html(root_dir=root_dir)
        except Exception as e:
            print(f'Error generating subjects data HTML file:\n    {e}')

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
        self.generate_html()
        self.generate_prof_html()
        self.generate_subjects_html()
        self.open_explorer()


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
        self.generate_results_html_open_explorer()


    def run(self):
        """
        Run the main application.
        """
        print("Running application...")
        self.lock_gui()
        self.running_spinner.start()

        self.thread = QThread()
        self.worker = main_worker.Worker()
        self.worker.setInput(root_dir=self.root_dir, doc_dir=self.doc_dir, clean_tmp=self.clean_tmp, copy_files=self.copy_files)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress_bar_visibility.connect(self.setProgressBarVisible)
        self.worker.progress_bar_value.connect(self.setProgressBarValue)
        self.worker.updated_results.connect(self.update_results)
        self.worker.update_errors.connect(self.update_errors)
        self.worker.update_doc_map.connect(self.update_doc_map)
        # self.worker.finished.connect(self.update_results)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.finished_run)
        self.thread.start()





def window(root_dir):
    app = QApplication(sys.argv)
    win = MainWindow(root_dir=root_dir)
    win.show()
    win.center()
    sys.exit(app.exec_())


# window()