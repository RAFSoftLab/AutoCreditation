"""
GUI application for AutoCreditation.
"""

import json
import os
from pathlib import Path
import sys
import time
from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import QPixmap, QFont
import PyQt5.QtGui as QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QDesktopWidget, QMessageBox, QTextEdit, QWidget, QLabel, QComboBox
# TODO Remove after debugging:
# import debugpy
from pyqtspinner.spinner import WaitingSpinner

import src.directory_reading as directory_reading

dirName = os.path.dirname(__file__)



class MainWindow(QMainWindow):
    """
    Main window of the application.
    """

    def __init__(self, root_dir):
        super(MainWindow, self).__init__()
        doc_dir = ''
        root_dir = root_dir
        print(root_dir)
        self.initUI(root_dir=root_dir, doc_dir=doc_dir)

    def initUI(self, root_dir='', doc_dir=''):
        self.setWindowTitle("AutoCreditation")
        self.setGeometry(100, 100, 1000, 800)
        # TODO: resizable window?
        self.setFixedSize(1000, 800)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(os.path.join(dirName, Path("resources/raf_logo_win.png"))), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.setWindowIcon(icon)
        # self.setStyleSheet("background-color: rgb(255, 255, 255);")

        self.root_dir = root_dir
        self.doc_dir = doc_dir
        self.valid_doc_dir = False
        self.clean_tmp = True
        self.output_text = ''

        self.center()

        # # # - - - GUI elements - - - # # #

        self.doc_dir_label = QtWidgets.QLabel(self)
        self.doc_dir_label.setText("Documentation directory:")
        self.doc_dir_label.move(10, 10)
        self.doc_dir_label.adjustSize()

        # Documentation directory path label
        self.doc_dir_text_line = QtWidgets.QLineEdit(self)
        self.doc_dir_text_line.setText(self.doc_dir)
        self.doc_dir_text_line.setFixedWidth(480)
        self.doc_dir_text_line.move(10, 30)
        self.doc_dir_text_line.setToolTip("Select the folder where the documentation files are located.")
        self.doc_dir_text_line.textChanged.connect(self.update_doc_dir)
        self.doc_dir_text_line.textChanged.connect(self.update_valid_doc_dir)

        # Documentation directory selection button
        self.choose_doc_dir_button = QtWidgets.QPushButton(self)
        self.choose_doc_dir_button.setText("Choose directory")
        self.choose_doc_dir_button.move(500, 30)
        self.choose_doc_dir_button.setFixedWidth(150)
        self.choose_doc_dir_button.clicked.connect(self.choose_doc_dir)

        # Run button
        self.run_button = QtWidgets.QPushButton(self)
        self.run_button.setText("Run")
        self.run_button.move(500, 60)
        self.run_button.setFixedWidth(150)
        self.set_run_button_enabled(False)
        self.run_button.clicked.connect(self.run)

        # Valid directory check label
        self.valid_doc_dir_label = QtWidgets.QLabel(self)
        self.update_valid_doc_dir()
        self.valid_doc_dir_label.move(10, 60)
        self.valid_doc_dir_label.adjustSize()

        # Clean /tmp directory
        self.clean_tmp_checkbox = QtWidgets.QCheckBox(self)
        self.clean_tmp_checkbox.setText("Clean /tmp directory")
        self.clean_tmp_checkbox.adjustSize()
        self.clean_tmp_checkbox.setToolTip("Clean the /tmp directory before running the application.")
        self.clean_tmp_checkbox.move(660, 35)
        self.clean_tmp_checkbox.setChecked(True)
        self.clean_tmp_checkbox.clicked.connect(self.update_clean_tmp)

        # Results and output text area
        self.results_text_area = QTextEdit(self)
        self.results_text_area.setReadOnly(True)
        self.results_text_area.move(10, 130)
        self.results_text_area.resize(980, 650)

        # Running spinner
        self.running_spinner = WaitingSpinner(self.results_text_area, True, True, Qt.ApplicationModal)

        # Progress bar
        self.progress_bar = QtWidgets.QProgressBar(self)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setGeometry(QtCore.QRect(10, 100, 200, 20))
        self.progress_bar.setVisible(False)

        # Progress description
        self.progress_desc_label = QLabel(self)
        self.progress_desc_label.setFixedHeight(20)
        self.progress_desc_label.setText('')
        # self.progress_desc_label.setAlignment(Qt.AlignCenter)
        self.progress_desc_label.move(230, 100)
        self.progress_desc_label.adjustSize()

        # Logo
        self.logo_label = QLabel(self)
        self.logo_label.setPixmap(QPixmap(os.path.join(dirName, Path("resources/raf_logo_no_bg.png"))).scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.logo_label.adjustSize()
        self.logo_label.move(self.width() - 10 - self.logo_label.width(), self.results_text_area.y() - self.logo_label.height() - 5)
        self.logo_label.show()

    # # # - - - GUI functions - - - # # #

    def center(self):
        """
        Center the window on the screen.
        """
        cp = QDesktopWidget().availableGeometry().center()
        wPos = self.frameGeometry()
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
        doc_dir = QtWidgets.QFileDialog.getExistingDirectory(self, "Select folder")
        self.update_doc_dir_text_line(doc_dir)

    def update_valid_doc_dir(self):
        """
        Check if the documentation directory is valid, and update the valid_doc_dir_label accordingly.
        """
        self.valid_doc_dir = True if self.doc_dir != '' and os.path.isdir(self.doc_dir) else False
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

    def set_run_button_enabled(self, enabled):
        """
        Enable or disable the run button.
        """
        self.run_button.setEnabled(enabled)

    def update_clean_tmp(self):
        """
        Clean the /tmp directory.
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
                    self.output_text += '\n- - - {}: \n{}\n- - -\n'.format(key, json.dumps(results[key], indent=4))
                    continue
                if type(results[key]) == list:
                    self.output_text += '\n- - - {}: \n{}\n- - -\n'.format(key, '\n'.join(results[key]))
                    continue
                self.output_text += '\n{}'.format(str(results[key]))
            self.results_text_area.setText(self.output_text)
        elif type(results) == list:
            self.results_text_area.setText('\n'.join(results))
        else:
            self.results_text_area.setText(str(results))

    # @QtCore.pyqtSlot()
    def lock_gui(self, lock=True):
        """
        Lock the GUI elements of the main window.
        """
        self.doc_dir_text_line.setEnabled(not lock)
        self.choose_doc_dir_button.setEnabled(not lock)
        self.run_button.setEnabled(not lock)
        if lock == True:
            self.run_button.setText("Running...")
        else:
            self.run_button.setText("Run")

    def finished_run(self):
        """
        Called when the run is finished.
        """
        self.lock_gui(lock=False)
        self.running_spinner.stop()

    def run(self):
        """
        Run the main application.
        """
        print("Running application...")
        self.lock_gui()
        self.running_spinner.start()

        # TODO: main runner function. Run scripts, generate results, etc.
        # separate thread
        # lock gui elements of main window (disable buttons, ligit conne edits, etc.)
        self.thread = QThread()
        self.worker = Worker()
        self.worker.setInput(root_dir=self.root_dir, doc_dir=self.doc_dir, clean_tmp=self.clean_tmp)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress_bar_visibility.connect(self.setProgressBarVisible)
        self.worker.progress_bar_value.connect(self.setProgressBarValue)
        self.worker.finished.connect(self.update_results)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.finished_run)
        self.thread.start()





# Runner/worker thread
class Worker(QObject):
    """
    Worker thread for the application.
    """
    # TODO Remove after debugging:
    # debugpy.debug_this_thread()
    finished = pyqtSignal(dict)
    progress_bar_visibility = pyqtSignal(bool)
    progress_bar_value = pyqtSignal(int, str)
    def setInput(self, root_dir, doc_dir, clean_tmp):
        self.root_dir = root_dir
        self.doc_dir = doc_dir
        self.clean_tmp = clean_tmp
        self.resultData = {}

    def run(self):
        print("Running main script...")
        self.progress_bar_visibility.emit(True)
        self.progress_bar_value.emit(0, 'Copying documentation files and reading directory structure...')
        # TODO: main script
        # Directory reading
        doc_structure, dir_tree = directory_reading.copy_read_doc_dir(root_dir=self.root_dir, documentation_dir=self.doc_dir, clear_dir=self.clean_tmp, overwrite=True, load_struct=True)
        # Reading main documentation file
        self.progress_bar_value.emit(30, 'Reading main documentation file...')

        # TODO: remove after testing
        time.sleep(5)

        self.resultData["doc_structure"] = doc_structure
        self.resultData["dir_tree"] = dir_tree
        print("Script finished.")
        self.progress_bar_visibility.emit(False)
        self.finished.emit(self.resultData)


def window(root_dir):
    app = QApplication(sys.argv)
    win = MainWindow(root_dir=root_dir)
    win.show()
    sys.exit(app.exec_())


# window()