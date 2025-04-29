"""
Main worker thread for the application.
Documentation copying, directory reading, file conversion and reading, hyperlinks verification, professors and subjects data comparison and filtering.
"""

import os
from pathlib import Path
import sys
# import debugpy
import json

from PyQt5 import QtCore
from PyQt5.QtCore import *

import src.directory_reading as directory_reading
import src.util as util
import src.docx_to_md_html as docx_to_md_html
import src.cyrillyc_to_latin as cyrillic_to_latin
import src.verify_data as verify_data
import src.doc_2_docx_ms_word_win as doc_2_docx_ms_word_win



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
    updated_results = pyqtSignal(dict)
    update_errors = pyqtSignal(list)
    update_doc_map = pyqtSignal(dict)
    def setInput(self, root_dir, doc_dir, clean_tmp, copy_files, processing_options):
        self.root_dir = root_dir
        self.doc_dir = doc_dir
        self.clean_tmp = clean_tmp
        self.copy_files = copy_files
        self.processing_options = processing_options
        self.files_dir = ''
        self.doc_map = {}
        self.resultData = {}
        self.errors = []

    def run(self):
        print("Running main script...")
        self.progress_bar_visibility.emit(True)

        self.updated_results.emit({'run_dir': f"Verification for documents in root directory: {self.doc_dir}"})

        if self.clean_tmp == True:
            self.progress_bar_value.emit(0, 'Clearing /tmp directory...')
            util.clear_tmp_dir(root_dir=self.root_dir)
            print('Cleared /tmp directory')

        self.progress_bar_value.emit(0 if self.clean_tmp == False else 2, 'Copying documentation files and reading directory structure...')
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
        # If the main documentation file is .doc, it is converted to .docx
        if main_doc['path'].split(os.sep)[-1].endswith('.doc'):
            self.progress_bar_value.emit(15, 'Converting main documentation file to .docx...')
            main_doc_docx = doc_2_docx_ms_word_win.doc2docx(doc_path=main_doc['path'], docx_path=os.path.join(self.root_dir, Path('tmp/converted_documents_docx'), main_doc['name'].replace('.doc', '.docx')))
            self.updated_results.emit({'Main documentation file converted to .docx: ': main_doc_docx})
            print(f'Main documentation file converted to .docx: {main_doc_docx}')
            self.doc_map[main_doc['path']] = main_doc_docx
            self.update_doc_map.emit(self.doc_map)
        doc_to_convert_path = self.doc_map[main_doc['path']] if main_doc['path'] in self.doc_map.keys() else main_doc['path']
        self.progress_bar_value.emit(20, 'Converting main documentation file to .html...')
        html_file = docx_to_md_html.convert_docx_file(root_dir=self.root_dir, docx_path=doc_to_convert_path, file_name='main_doc', processed_dir=Path('tmp/converted_documents_md_html'), clear_dir=True, output_format='html')
        self.updated_results.emit({'Main documentation file converted to .html: ': html_file})
        # self.updated_results.emit(md_file)
        print(f'Main documentation file converted to .html: {html_file}')

        # Reading converted file and converting cyrillic characters to latin characters
        self.progress_bar_value.emit(25, 'Converting cyrillic characters to latin characters...')
        with open(html_file, 'r', encoding='utf-8') as f:
            html_file_txt = f.read()
            html_file_txt = cyrillic_to_latin.cyrillic_to_latin(html_file_txt)
        html_file_lat = html_file.replace('.html', '_lat.html')
        with open(html_file_lat, 'w', encoding='utf-8') as f:
            f.write(html_file_txt)

        # Finding studies program
        self.progress_bar_value.emit(27, 'Finding studies program...')
        studies_programme_and_type = util.find_studies_programme(root_dir=self.root_dir, html_file_lat=html_file_txt)
        self.updated_results.emit({'Studies programme': studies_programme_and_type['studies_programme'], 'Studies type': studies_programme_and_type['studies_type']})
        print(f"Studies programe: {studies_programme_and_type['studies_programme']}\nStudies type: {studies_programme_and_type['studies_type']}")


        # Finding hyperlinks to files
        self.progress_bar_value.emit(30, 'Finding hyperlinks to files...')
        found_hyperlinks = util.find_link_tags(root_dir=self.root_dir, doc_dir=self.files_dir, html_file_txt=html_file_txt, file_format='html')
        print(f"Found hyperlinks: \n{json.dumps(found_hyperlinks, indent=4)}")
        self.updated_results.emit({'Found hyperlinks': found_hyperlinks})

        # Verify hyperlinks files exist
        self.progress_bar_value.emit(35, 'Verifying hyperlinks files exist...')
        unmatched_hyperlinks = util.verify_hyperlinks(root_dir=self.root_dir, found_hyperlinks=found_hyperlinks)
        if len(unmatched_hyperlinks) > 0:
            self.errors.append({'Unmatched hyperlinks': unmatched_hyperlinks})
        print(f"Unmatched hyperlinks: \n{json.dumps(unmatched_hyperlinks, indent=4)}")
        self.updated_results.emit({'Unmatched hyperlinks': unmatched_hyperlinks if len(unmatched_hyperlinks) > 0 else 'All hyperlinks verified'})

        # File verification 1: "Knjiga nastavnika"
        self.progress_bar_value.emit(40, 'Finding professors file...')
        professors_file = verify_data.find_professors_file(root_dir=self.root_dir, links=found_hyperlinks)
        professors_file_txt, professors_data, professors_save_path = '', '', ''
        if professors_file != []:
            print(f"Professors file: {professors_file}")
            self.updated_results.emit({'Professors file': professors_file})
            # Verify link to professors file
            self.progress_bar_value.emit(45, 'Verifying professors file link...')
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
                professors_file_path = professors_file['path']
                if professors_file['path'].endswith('.doc') and sys.platform.startswith('win') or sys.platform.startswith('linux'):
                    self.progress_bar_value.emit(50, 'Converting professors file to .docx...')
                    file_name = professors_file['path'].split(os.sep)[-1]
                    professors_file_docx = doc_2_docx_ms_word_win.doc2docx(doc_path=professors_file['path'], docx_path=os.path.join(self.root_dir, Path('tmp/converted_documents_docx'), file_name.replace('.doc', '.docx')))
                    print(f'Converted professors file to .docx: {professors_file}')
                    self.doc_map[professors_file['path']] = professors_file_docx
                    self.updated_results.emit({'Professors file converted to .docx: ': professors_file_docx})
                    self.update_doc_map.emit(self.doc_map)
                    professors_file_path = self.doc_map[professors_file['path']]
                if professors_file_path.endswith('.docx'):
                    self.progress_bar_value.emit(55, 'Converting professors file to .html...')
                    professors_file = docx_to_md_html.convert_docx_file(root_dir=self.root_dir, docx_path=professors_file_path, file_name='professors_file', processed_dir='tmp/converted_documents_md_html', output_format='html')
                    print(f'Converted professors file to .html: {professors_file}')
                    self.progress_bar_value.emit(60, 'Converting cyrillic characters to latin characters...')
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
            self.progress_bar_value.emit(62, 'Listing professors file content...')
            print(f'Professors file loaded. Reading...')
            professors_data, professors_save_path = verify_data.read_professors(root_dir=self.root_dir, professors_file_txt=professors_file_txt)
            self.updated_results.emit({'Professors file read': professors_data})
            self.updated_results.emit({'Professors file saved to file': professors_save_path})

        # Find and read subjects file
        self.progress_bar_value.emit(65, 'Finding subjects file...')
        subjects_file = verify_data.find_subjects_file(root_dir=self.root_dir, links=found_hyperlinks)
        subjects_file_txt, subjects_data, subjects_save_path = '', '', ''
        print(f"Subjects file: {subjects_file}")
        subjects_file_verified = False
        if subjects_file != []:
            self.updated_results.emit({'Subjects file': subjects_file})
            # Verify path to subjects file
            self.progress_bar_value.emit(70, 'Verifying subjects file path...')
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
                self.progress_bar_value.emit(75, 'Converting subjects file to .docx...')
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
            self.progress_bar_value.emit(85, 'Converting cyrillic characters to latin characters...')
            print('Converting cyrillic characters to latin characters...')
            with open(subjects_file, 'r', encoding='utf-8') as f:
                subjects_file_txt = f.read()
                subjects_file_txt = cyrillic_to_latin.cyrillic_to_latin(subjects_file_txt)
            print('Saving file with latin characters...')
            with open(subjects_file.replace('.html', '_lat.html'), 'w', encoding='utf-8') as f:
                f.write(subjects_file_txt)
            if subjects_file_txt != '':
                self.progress_bar_value.emit(87, 'Listing subjects file content...')
                print(f'Subjects file loaded. Reading...')
                subjects_data, subjects_save_path = verify_data.read_subjects(root_dir=self.root_dir, subjects_file_txt=subjects_file_txt)
                self.updated_results.emit({'Subjects file read': subjects_data})
                self.updated_results.emit({'Subjects file saved to file': subjects_save_path})

        # Compare professors and subjects data
        if subjects_data != [] and professors_data != []:
            self.progress_bar_value.emit(90, 'Comparing professors and subjects data...')
            print('Comparing professors and subjects data...')
            compare_results = verify_data.compare_prof_and_subj_data(root_dir=self.root_dir, prof_data=professors_data, subj_data=subjects_data)
            self.updated_results.emit({'Professors and subjects data comparison': compare_results})
            self.progress_bar_value.emit(95, 'Filtering and sorting comparison results...')
            print('Filtering and sorting comparison results...')
            compare_results_filter = verify_data.filter_sort_results(root_dir=self.root_dir)
            self.updated_results.emit({'Filtered comparison results': compare_results_filter})

        print("Script finished.")
        self.progress_bar_visibility.emit(False)
        self.finished.emit(self.resultData)