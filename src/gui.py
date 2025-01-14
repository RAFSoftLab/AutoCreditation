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
import debugpy
from pyqtspinner.spinner import WaitingSpinner

import src.directory_reading as directory_reading
import src.util as util
import src.docx_to_md as docx_to_md
import src.cyrillyc_to_latin as cyrillic_to_latin
import src.verify_data as verify_data
import src.doc_2_docx_ms_word_win as doc_2_docx_ms_word_win

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
        # TODO: remove after testing:
        self.doc_dir = r'C:\Users\steva\Downloads\Softversko inzenjerstvo (OAS) - original-20241120T100738Z-001\Softversko inzenjerstvo (OAS) - original'
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
        self.clean_tmp_checkbox.move(660, 30)
        self.clean_tmp_checkbox.setFixedHeight(self.choose_doc_dir_button.height())
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
        if doc_dir != '':
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
        self.valid_doc_dir_label.adjustSize()

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
                    items_list = []
                    for item in results[key]:
                        if type(item) == str:
                            items_list.append(item)
                        elif type(item) == dict:
                            items_list.append(json.dumps(item, indent=4))
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
        if results != '':
            self.results_text_area.verticalScrollBar().setValue(self.results_text_area.verticalScrollBar().maximum())
        else:
            self.results_text_area.verticalScrollBar().setValue(0)

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
        self.worker.updated_results.connect(self.update_results)
        # TODO: new window for final results
        # self.worker.finished.connect(self.update_results)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.finished_run)
        self.thread.start()





# Runner/worker thread
class Worker(QObject):
    """
    Worker thread for the application.
    """
    # TODO Remove after debugging:
    debugpy.debug_this_thread()
    finished = pyqtSignal(dict)
    progress_bar_visibility = pyqtSignal(bool)
    progress_bar_value = pyqtSignal(int, str)
    updated_results = pyqtSignal(dict)
    update_errors = pyqtSignal(list)
    def setInput(self, root_dir, doc_dir, clean_tmp):
        self.root_dir = root_dir
        self.doc_dir = doc_dir
        self.clean_tmp = clean_tmp
        self.resultData = {}
        self.errors = []

    def run(self):
        print("Running main script...")
        self.progress_bar_visibility.emit(True)
        if self.clean_tmp == True:
            self.progress_bar_value.emit(0, 'Clearing /tmp directory...')
            util.clear_tmp_dir(root_dir=self.root_dir)
            print('Cleared /tmp directory')
        self.progress_bar_value.emit(0 if self.clean_tmp == False else 5, 'Copying documentation files and reading directory structure...')
        # TODO: main script
        # Directory reading
        doc_structure, dir_tree, files_dir = directory_reading.copy_read_doc_dir(root_dir=self.root_dir, documentation_dir=self.doc_dir, clear_dir=self.clean_tmp, overwrite=True, load_struct=True)
        # TODO: file conversion during directory reading (if possible)
        self.updated_results.emit({'Documentation directory structure': doc_structure})
        # Finding main documentation file
        self.progress_bar_value.emit(10, 'Finding main documentation file...')
        files_in_doc_dir = [i for i in doc_structure['contents'] if i['type'] == 'file']
        self.updated_results.emit({'Files in root directory: ': '\n'.join([i['name'] for i in files_in_doc_dir])})
        print("Files in documentation root directory:")
        for i in files_in_doc_dir:
            print(i['name'])
        main_doc = util.find_main_doc(docs=files_in_doc_dir)
        self.updated_results.emit({'Main document: ': main_doc['name']})
        print(f"Main documentation file: {main_doc['name']}")
        # Reading main documentation file
        self.progress_bar_value.emit(20, 'Converting main documentation file to .md...')
        md_file = docx_to_md.convert_docx_file(root_dir=self.root_dir, docx_path=main_doc['path'], file_name='main_doc', processed_dir=Path('tmp/converted_documents'), clear_dir=True, output_format='md')
        self.updated_results.emit({'Main documentation file converted to .md: ': md_file})
        # self.updated_results.emit(md_file)
        print(f'Main documentation file converted to .md: {md_file}')
        # Reading converted file and converting cyrillic characters to latin characters
        self.progress_bar_value.emit(30, 'Reading converted file and converting cyrillic characters to latin characters...')
        with open(md_file, 'r', encoding='utf-8') as f:
            md_file_txt = f.read()
            md_file_txt = cyrillic_to_latin.cyrillic_to_latin(md_file_txt)
        md_file_lat = md_file.replace('.md', '_lat.md')
        with open(md_file_lat, 'w', encoding='utf-8') as f:
            f.write(md_file_txt)
        self.progress_bar_value.emit(40, 'Finding hyperlinks to files...')
        found_hyperlinks = util.find_link_tags(root_dir=self.root_dir, md_file_txt=md_file_txt)
        print(f"Found hyperlinks: \n{json.dumps(found_hyperlinks, indent=4)}")
        self.updated_results.emit({'Found hyperlinks': found_hyperlinks})
        # Verify hyperlinks files exist
        self.progress_bar_value.emit(45, 'Verifying hyperlinks files exist...')
        unmatched_hyperlinks = util.verify_hyperlinks(root_dir=self.root_dir, found_hyperlinks=found_hyperlinks)
        if len(unmatched_hyperlinks) > 0:
            self.errors.append({'Unmatched hyperlinks': unmatched_hyperlinks})
        print(f"Unmatched hyperlinks: \n{json.dumps(unmatched_hyperlinks, indent=4)}")
        self.updated_results.emit({'Unmatched hyperlinks': unmatched_hyperlinks if len(unmatched_hyperlinks) > 0 else 'All hyperlinks verified'})
        # TODO: file verification (file content)
        # File verification 1: "Knjiga nastavnika"
        self.progress_bar_value.emit(50, 'Finding professors file...')
        professors_file = verify_data.find_professors_file(root_dir=self.root_dir, links=found_hyperlinks)
        professors_file_txt = ''
        if professors_file != []:
            print(f"Professors file: {professors_file}")
            self.updated_results.emit({'Professors file': professors_file})
            # Verify link to professors file
            self.progress_bar_value.emit(55, 'Verifying professors file link...')
            if os.path.exists(professors_file['path']) or os.path.exists(professors_file['path'].replace('.doc', '.docx')):
                if os.path.exists(professors_file['path'].replace('.doc', '.docx')):
                    print('Updating professors file path to .docx...')
                    for indexI, link in enumerate(found_hyperlinks):
                        if link['path'] == professors_file['path']:
                            found_hyperlinks[indexI]['path'] = professors_file['path'].replace('.doc', '.docx')
                            util.update_hyperlinks(root_dir=self.root_dir, new_hyperlinks=found_hyperlinks)
                self.updated_results.emit({'Professors file link verification': 'File exists'})
                print(f'Professors file link verified - file found: {professors_file["path"]}')
                # Read professors file
                self.progress_bar_value.emit(60, 'Reading professors file...')
                if professors_file['path'].endswith('.doc') and sys.platform.startswith('win'):
                    file_name = professors_file['path'].split(os.sep)[-1]
                    professors_file['path'] = doc_2_docx_ms_word_win.doc2docx(doc_path=professors_file['path'], docx_path=os.path.join(self.root_dir, Path('tmp/converted_documents'), file_name.replace('.doc', '.docx')))
                    print(f'Converted professors file to .docx: {professors_file}')
                if professors_file['path'].endswith('.docx'):
                    self.progress_bar_value.emit(65, 'Converting professors file to .md and reading it...')
                    professors_file = docx_to_md.convert_docx_file(root_dir=self.root_dir, docx_path=professors_file['path'], file_name='professors_file', output_format='md')
                    print(f'Converted professors file to .md: {professors_file}')
                    print('Converting cyrillic characters to latin characters...')
                    with open(professors_file, 'r', encoding='utf-8') as f:
                        professors_file_txt = f.read()
                        professors_file_txt = cyrillic_to_latin.cyrillic_to_latin(professors_file_txt)
                    print('Saving file with latin characters...')
                    with open(professors_file.replace('.md', '_lat.md'), 'w', encoding='utf-8') as f:
                        f.write(professors_file_txt)
                else:
                    print(f'Professors file is not .docx. Skipping conversion and reading.')
                    self.errors.append({'Professors file': 'Not .docx'})
                    self.updated_results.emit({'Professors file': 'Not .docx'})
            else:
                self.updated_results.emit({'Professors file link verification': 'File does not exist or link is broken'})
                self.errors.append({'Professors file link verification': 'File does not exist or link is broken'})
        else:
            print('Professors file not found. Skipping professors verification.')
            self.errors.append({'Professors file not found': 'Not found'})
            self.updated_results.emit({'Professors file: ': 'Not found'})
        if professors_file_txt != '':
            self.progress_bar_value.emit(70, 'Verifying professors file content...')
            print(f'Professors file loaded. Processing...')
            # TODO: verify professors file content






        print("Script finished.")
        self.progress_bar_visibility.emit(False)
        self.finished.emit(self.resultData)


def window(root_dir):
    app = QApplication(sys.argv)
    win = MainWindow(root_dir=root_dir)
    win.show()
    sys.exit(app.exec_())


# window()