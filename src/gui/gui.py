"""
GUI application for AutoCreditation
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
from PyQt5.QtWidgets import QApplication, QMainWindow, QSystemTrayIcon, QPushButton, QDesktopWidget, QLineEdit, QTextEdit, QWidget, QLabel, QCheckBox, QGridLayout, QVBoxLayout, QProgressBar
# TODO Remove after debugging:
import debugpy
from pyqtspinner.spinner import WaitingSpinner

import src.directory_reading as directory_reading
import src.util as util
import src.docx_to_md_html as docx_to_md_html
import src.cyrillyc_to_latin as cyrillic_to_latin
import src.verify_data as verify_data
import src.doc_2_docx_ms_word_win as doc_2_docx_ms_word_win

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
        # TODO: remove after testing:
        self.doc_dir = r'C:/Users/steva/Downloads/Softversko inzenjerstvo (OAS) - original-20241120T100738Z-001/Softversko inzenjerstvo (OAS) - original'
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
        self.choose_doc_dir_button.move(500, 30)
        # self.choose_doc_dir_button.setFixedWidth(150)
        self.choose_doc_dir_button.setMinimumWidth(150)
        self.choose_doc_dir_button.clicked.connect(self.choose_doc_dir)
        self.control_panel.addWidget(self.choose_doc_dir_button, 1, 3)

        # Run button
        self.run_button = QPushButton(self)
        self.run_button.setText("Run")
        self.run_button.move(500, 60)
        # self.run_button.setFixedWidth(150)
        self.run_button.setMinimumWidth(150)
        self.set_run_button_enabled(False)
        self.run_button.clicked.connect(self.run)
        self.control_panel.addWidget(self.run_button, 2, 3)

        # Results button
        self.results_button = QPushButton(self)
        self.results_button.setText("Results")
        self.results_button.move(660, 90)
        self.results_button.setMinimumWidth(150)
        self.results_button.setEnabled(self.finished)
        # TODO:
        # self.results_button.clicked.connect(self.results)
        self.control_panel.addWidget(self.results_button, 2, 4)

        # Valid directory check label
        self.valid_doc_dir_label = QLabel(self)
        self.update_valid_doc_dir()
        self.valid_doc_dir_label.move(10, 60)
        self.valid_doc_dir_label.adjustSize()
        self.control_panel.addWidget(self.valid_doc_dir_label, 2, 0, 1, 3, alignment=Qt.AlignmentFlag.AlignTop)

        # Clean /tmp directory
        self.clean_tmp_checkbox = QCheckBox(self)
        self.clean_tmp_checkbox.setText("Clean /tmp directory")
        self.clean_tmp_checkbox.adjustSize()
        self.clean_tmp_checkbox.setToolTip("Clean the /tmp directory before running the application.")
        self.clean_tmp_checkbox.move(660, 30)
        self.clean_tmp_checkbox.setFixedHeight(self.choose_doc_dir_button.height())
        self.clean_tmp_checkbox.setChecked(True)
        self.clean_tmp_checkbox.clicked.connect(self.update_clean_tmp)
        self.control_panel.addWidget(self.clean_tmp_checkbox, 1, 4, 1, 2)

        # Results and output text area
        self.results_text_area = QTextEdit(self)
        self.results_text_area.setReadOnly(True)
        # self.results_text_area.move(10, 130)
        # self.results_text_area.resize(980, 800)
        self.results_text_area.setMinimumHeight(self.results_text_area.fontMetrics().height() * 30)
        self.results_text_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.results_text_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.output_panel.addWidget(self.results_text_area, 0, 0)

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

        self.main_layout.addLayout(self.control_panel_area, stretch=1)
        self.main_layout.addLayout(self.output_panel, stretch=2)
        # self.main_layout.setRowStretch(0, 0)
        # self.main_layout.setRowStretch(1, 1)
        self.central_widget.setLayout(self.main_layout)

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
        if results != '':
            self.results_text_area.verticalScrollBar().setValue(self.results_text_area.verticalScrollBar().maximum())
        else:
            self.results_text_area.verticalScrollBar().setValue(0)

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
        self.finished = True
        self.results_button.setEnabled(True)

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
        self.worker.setInput(root_dir=self.root_dir, doc_dir=self.doc_dir, clean_tmp=self.clean_tmp, copy_files=self.copy_files)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress_bar_visibility.connect(self.setProgressBarVisible)
        self.worker.progress_bar_value.connect(self.setProgressBarValue)
        self.worker.updated_results.connect(self.update_results)
        self.worker.update_errors.connect(self.update_errors)
        self.worker.update_doc_map.connect(self.update_doc_map)
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
    update_doc_map = pyqtSignal(dict)
    def setInput(self, root_dir, doc_dir, clean_tmp, copy_files):
        self.root_dir = root_dir
        self.doc_dir = doc_dir
        self.clean_tmp = clean_tmp
        self.copy_files = copy_files
        self.files_dir = ''
        self.doc_map = {}
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
        # Directory reading
        doc_structure, dir_tree, self.files_dir = directory_reading.copy_read_doc_dir(root_dir=self.root_dir, documentation_dir=self.doc_dir, clear_dir=self.clean_tmp, overwrite=True, load_struct=True, convert_names_to_latin=True)
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
        self.progress_bar_value.emit(20, 'Converting main documentation file to .html...')
        # If the main documentation file is .doc, it is converted to .docx
        if main_doc['path'].split(os.sep)[-1].endswith('.doc'):
            main_doc_docx = doc_2_docx_ms_word_win.doc2docx(doc_path=main_doc['path'], docx_path=os.path.join(self.root_dir, Path('tmp/converted_documents_docx'), main_doc['name'].replace('.doc', '.docx')))
            self.updated_results.emit({'Main documentation file converted to .docx: ': main_doc_docx})
            print(f'Main documentation file converted to .docx: {main_doc_docx}')
            self.doc_map[main_doc['path']] = main_doc_docx
            self.update_doc_map.emit(self.doc_map)
        doc_to_convert_path = self.doc_map[main_doc['path']] if main_doc['path'] in self.doc_map.keys() else main_doc['path']
        md_file = docx_to_md_html.convert_docx_file(root_dir=self.root_dir, docx_path=doc_to_convert_path, file_name='main_doc', processed_dir=Path('tmp/converted_documents_md_html'), clear_dir=True, output_format='html')
        self.updated_results.emit({'Main documentation file converted to .html: ': md_file})
        # self.updated_results.emit(md_file)
        print(f'Main documentation file converted to .html: {md_file}')

        # Reading converted file and converting cyrillic characters to latin characters
        self.progress_bar_value.emit(30, 'Reading converted file and converting cyrillic characters to latin characters...')
        with open(md_file, 'r', encoding='utf-8') as f:
            md_file_txt = f.read()
            md_file_txt = cyrillic_to_latin.cyrillic_to_latin(md_file_txt)
        md_file_lat = md_file.replace('.html', '_lat.html')
        with open(md_file_lat, 'w', encoding='utf-8') as f:
            f.write(md_file_txt)

        # Finding hyperlinks to files
        self.progress_bar_value.emit(40, 'Finding hyperlinks to files...')
        found_hyperlinks = util.find_link_tags(root_dir=self.root_dir, doc_dir=self.files_dir, md_file_txt=md_file_txt, file_format='html')
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
        professors_file_txt, professors_data, professors_save_path = '', '', ''
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
                professors_file_path = professors_file['path']
                # TODO: remove platform check
                # TODO: move to separate function?
                if professors_file['path'].endswith('.doc') and sys.platform.startswith('win') or sys.platform.startswith('linux'):
                    file_name = professors_file['path'].split(os.sep)[-1]
                    professors_file_docx = doc_2_docx_ms_word_win.doc2docx(doc_path=professors_file['path'], docx_path=os.path.join(self.root_dir, Path('tmp/converted_documents_docx'), file_name.replace('.doc', '.docx')))
                    print(f'Converted professors file to .docx: {professors_file}')
                    self.doc_map[professors_file['path']] = professors_file_docx
                    self.updated_results.emit({'Professors file converted to .docx: ': professors_file_docx})
                    self.update_doc_map.emit(self.doc_map)
                    professors_file_path = self.doc_map[professors_file['path']]
                if professors_file_path.endswith('.docx'):
                    self.progress_bar_value.emit(65, 'Converting professors file to .html and reading it...')
                    professors_file = docx_to_md_html.convert_docx_file(root_dir=self.root_dir, docx_path=professors_file_path, file_name='professors_file', processed_dir='tmp/converted_documents_md_html', output_format='html')
                    print(f'Converted professors file to .html: {professors_file}')
                    print('Converting cyrillic characters to latin characters...')
                    with open(professors_file, 'r', encoding='utf-8') as f:
                        professors_file_txt = f.read()
                        professors_file_txt = cyrillic_to_latin.cyrillic_to_latin(professors_file_txt)
                    print('Saving file with latin characters...')
                    with open(professors_file.replace('.html', '_lat.html'), 'w', encoding='utf-8') as f:
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
            self.progress_bar_value.emit(70, 'Listing professors file content...')
            print(f'Professors file loaded. Reading...')
            professors_data, professors_save_path = verify_data.read_professors(root_dir=self.root_dir, professors_file_txt=professors_file_txt)
            self.updated_results.emit({'Professors file read': professors_data})
            self.updated_results.emit({'Professors file saved to file': professors_save_path})

        # Find and read subjects file
        self.progress_bar_value.emit(75, 'Finding subjects file...')
        subjects_file = verify_data.find_subjects_file(root_dir=self.root_dir, links=found_hyperlinks)
        subjects_file_txt, subjects_data, subjects_save_path = '', '', ''
        print(f"Subjects file: {subjects_file}")
        subjects_file_verified = False
        if subjects_file != []:
            self.updated_results.emit({'Subjects file': subjects_file})
            # Verify path to subjects file
            self.progress_bar_value.emit(77, 'Verifying subjects file path...')
            if os.path.exists(subjects_file['path']):
                subjects_file_verified = True
                print(f'Subjects file path verified - file found: {subjects_file["path"]}')
                self.updated_results.emit({'Subjects file link verification': 'File exists'})
        else:
            self.updated_results.emit({'Subjects file': 'Not found'})
            self.errors.append({'Subjects file not found': 'Not found'})
        if subjects_file_verified == True:
            subjects_file_path = subjects_file['path']
            if subjects_file['path'].endswith('.doc'):
                # Convert subjects file to .docx
                self.progress_bar_value.emit(78, 'Converting subjects file to .docx...')
                subjects_file_docx = doc_2_docx_ms_word_win.doc2docx(doc_path=subjects_file['path'], docx_path=os.path.join(self.root_dir, Path('tmp/converted_documents_docx'), subjects_file['path'].split(os.sep)[-1].replace('.doc', '.docx')))
                print(f'Converted subjects file to .docx: {subjects_file}')
                self.doc_map[subjects_file['path']] = subjects_file_docx
                self.updated_results.emit({'Subjects file converted to .docx: ': subjects_file_docx})
                self.update_doc_map.emit(self.doc_map)
                subjects_file_path = self.doc_map[subjects_file['path']]
            # Convert subjects file to .html
            self.progress_bar_value.emit(80, 'Converting subjects file to .html...')
            subjects_file = docx_to_md_html.convert_docx_file(root_dir=self.root_dir, docx_path=subjects_file_path, file_name='subjects_file', processed_dir='tmp/converted_documents_md_html', output_format='html')
            print(f'Converted subjects file to .html: {subjects_file}')
            print('Converting cyrillic characters to latin characters...')
            with open(subjects_file, 'r', encoding='utf-8') as f:
                subjects_file_txt = f.read()
                subjects_file_txt = cyrillic_to_latin.cyrillic_to_latin(subjects_file_txt)
            print('Saving file with latin characters...')
            with open(subjects_file.replace('.html', '_lat.html'), 'w', encoding='utf-8') as f:
                f.write(subjects_file_txt)
            if subjects_file_txt != '':
                self.progress_bar_value.emit(82, 'Listing subjects file content...')
                print(f'Subjects file loaded. Reading...')
                subjects_data, subjects_save_path = verify_data.read_subjects(root_dir=self.root_dir, subjects_file_txt=subjects_file_txt)
                self.updated_results.emit({'Subjects file read': subjects_data})
                self.updated_results.emit({'Subjects file saved to file': subjects_save_path})

        # Compare professors and subjects data
        if subjects_data != [] and professors_data != []:
            self.progress_bar_value.emit(85, 'Comparing professors and subjects data...')
            print('Comparing professors and subjects data...')
            compare_results = verify_data.compare_prof_and_subj_data(root_dir=self.root_dir, prof_data=professors_data, subj_data=subjects_data)

            # TODO: add to gui results, to gui errors.







        print("Script finished.")
        # TODO: Delete copied files after finish.
        self.progress_bar_visibility.emit(False)
        self.finished.emit(self.resultData)


def Worker2(QObject):
    """
    Worker thread for results display.
    """
    # TODO


def window(root_dir):
    app = QApplication(sys.argv)
    win = MainWindow(root_dir=root_dir)
    win.show()
    sys.exit(app.exec_())


# window()