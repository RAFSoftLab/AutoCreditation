"""
Verification of data in the documentation files.
"""


import os
import pandas as pd
from pathlib import Path
import re

import src.util as util


def find_professors_file(root_dir, links, search_regex=''):
    """
    Finds the professors file in the given list of hyperlinks.

    Args:
        root_dir (str):          Root directory of the project, absolute path
        links (list):            List of hyperlinks
        search_regex (str):      (Optional) Regular expression to search for the professors file. If not passed, 'Knjiga\snastavnika' is used. Default is ''

    Returns:
        (dict):                  Professors file
    """
    professors_file = []

    search_regex = r'Knjiga\snastavnika' if search_regex == '' else search_regex

    for link in links:
        if re.search(r'Knjiga\snastavnika', f'{link['name']} {link["desc"]} {link["line"]}'):
            professors_file.append(link)

    if len(professors_file) > 1:
        print('Multiple professors files found')
        for prof_file in professors_file:
            if re.search(search_regex, prof_file['path']):
                print(f'Professors file found: {prof_file["path"]}')
                return prof_file

    return professors_file[0] if len(professors_file) > 0 else []

def find_subjects_file(root_dir, links, search_regex=''):
    """
    Finds the subjects file in the given list of hyperlinks.

    Args:
        root_dir (str):          Root directory of the project, absolute path
        links (list):            List of hyperlinks
        search_regex (str):      (Optional) Regular expression to search for the subjects file. If not passed, 'Spisak predmeta' is used. Default is ''

    Returns:
        (dict):                  Subjects file
    """
    subjects_file = []

    search_regex = r'Knjiga\spredmeta' if search_regex == '' else search_regex

    for link in links:
        if re.search(search_regex, f'{link["name"]} {link["desc"]} {link["line"]}') and re.search(r'Tabela', link['name'], re.I):
            subjects_file.append(link)

    return subjects_file[0] if len(subjects_file) > 0 else []

def extract_proffesor_table(prof_table):
    """
    Extracts professor table data from the given table.

    Args:
        prof_table (array):       Professor table
    Returns:
        (dict):                   Professor table data with keys 'name', 'title', 'institution', 'sci_discipline', 'subjects', 'subjects_header'
    """

    prof_name, prof_title, institution, sci_discipline = '', '', '', ''
    subjects, subjects_header = [], []
    in_subjects, index_subject_row = False, 0
    for index, row in enumerate(prof_table.values):
        if len(row) < 1:
            continue
        if prof_name == '' and True not in [True if re.search(r'Ime i prezime', elem) else False for elem in row]:
            continue
        row_elems = set()
        row = [elem for elem in row if elem not in row_elems and type(elem) == str and (row_elems.add(elem) or True)]
        if prof_name == '':
            prof_name = row[1] if len(row) > 1 else row[0] if len(row) > 0 else ''
            continue
        if prof_title == '':
            prof_title = row[2] if len(row) > 2 else row[1] if len(row) > 1 else row[0] if len(row) > 0 else ''
            continue
        if institution == '':
            institution = row[3] if len(row) > 3 else row[2] if len(row) > 2 else row[1] if len(row) > 1 else row[0] if len(row) > 0 else ''
            continue
        if sci_discipline == '':
            sci_discipline = row[4] if len(row) > 4 else row[3] if len(row) > 3 else row[2] if len(row) > 2 else row[1] if len(row) > 1 else row[0] if len(row) > 0 else ''
            continue
        if in_subjects == True and True in [(True if re.search(r'Reprezentativne\sreference', re.sub(r'\s+', ' ', elem.strip()), re.I) else False) if type(elem) == str else False for elem in row]:
            in_subjects = False
            # Finishes reading current table. For reading other values, replace 'break' with 'continue' and add neccessary code.
            break
        if in_subjects == False and not True in [(True if re.search(r'Spisak\spredmeta.*?akreditovan', re.sub(r'\s+', ' ', elem.strip()), re.I) else False) if type(elem) == str else False for elem in row]:
            continue
        elif in_subjects == False:
            in_subjects = True
            continue
        if index_subject_row == 0:
            subjects_header = row
            index_subject_row += 1
            continue
        index_subject = row[0].strip().replace('.', '') if len(row) > 0 else ''
        subject_code = row[1].strip() if len(row) > 1 else ''
        subject_name = row[2].strip() if len(row) > 2 else ''
        subject_type = row[3].strip() if len(row) > 3 else ''
        subject_programme = row[4].strip() if len(row) > 4 else ''
        subject_studies_type = row[5].strip() if len(row) > 5 else ''
        if subject_name != '':
            subjects.append({'index': index_subject, 'code': subject_code, 'name': subject_name, 'type': subject_type, 'studies_programme': subject_programme, 'studies_type': subject_studies_type})
        index_subject_row += 1
    return {'name': prof_name, 'title': prof_title, 'institution': institution, 'sci_discipline': sci_discipline, 'subjects': subjects, 'subjects_header': subjects_header}

def extract_subjects_table(subj_table):
    """
    Extracts subjects table data from the given table.
    """
    # TODO
    return {}

def read_professors(root_dir, professors_file_txt):
    """
    Reads contents of the professors file. Created a list of tables, with each table represented by a dictionary.
    First table is a list of professors (keys are 'ord_num', 'prof_name', 'prof_title').
    Other tables are professor tables (keys are 'name', 'title', 'institution', 'sci_discipline', 'subjects', 'subjects_header').

    Args:
        root_dir (str):              Root directory of the project, absolute path
        professors_file_txt (str):   Text of the professors file
    Returns:
        (list):                      List of tables (each table represented by a dictionary)
    """


    tables_in_file = re.findall(r'\<table\>.*?\<\/table\>', professors_file_txt)
    read_tables = []
    prof_tables = []
    table_data = []

    for indexTable, table in enumerate(tables_in_file):
        table_read = pd.read_html(table)[0]
        # table_read.to_csv(os.path.join(root_dir, Path('tmp/converted_documents_md_html/curr_table.txt', sep='\t', index=False)))
        read_tables.append(table_read)
        print(table_read)
        if indexTable == 0:
            # First table is a list of professors
            header = table_read.values[0]
            header_elems = set()
            header = [elem for elem in header if elem not in header_elems and type(elem) == str and (header_elems.add(elem) or True)]
            table_vals = []
            for index, row in enumerate(table_read.values[1:]):
                ord_num = row[0].replace('.', '') if len(row) > 0 else ''
                jmbg = row[1] if len(row) > 1 else ''
                prof_name = row[2] if len(row) > 1 else ''
                prof_title = row[3] if len(row) > 2 else ''
                table_vals.append({'ord_num': ord_num, 'prof_name': prof_name, 'prof_title': prof_title})
            table_data.append({'type': 'prof_list', 'data': table_vals, 'header': header})
            continue
        # Other tables are professor tables
        professor_table = extract_proffesor_table(prof_table=table_read)
        prof_tables.append(professor_table)
    table_data.append({'type': 'prof_tables', 'data': prof_tables, 'header': prof_tables[0]['subjects_header'] if len(prof_tables) > 0 else []})
    # Save found data
    save_path = util.save_data(root_dir=root_dir, data=table_data, save_dir='tmp', data_name='professors_data')
    print(f'Saved professors data to {save_path}')
    return table_data, save_path

def read_subjects(root_dir, subjects_file_txt):
    """
    Reads contents of the subjects file. Created a list of tables, with each table represented by a dictionary.
    First table is a list of subjects (keys are 'index', 'code', 'name', 'type', 'studies_programme', 'studies_type').
    Other tables are subjects tables (keys are 'name', 'title', 'institution', 'sci_discipline', 'subjects', 'subjects_header').

    Args:
        root_dir (str):              Root directory of the project, absolute path
        subjects_file_txt (str):     Text of the subjects file
    Returns:
        (list):                      List of tables (each table represented by a dictionary)
    """

    tables_in_file = re.findall(r'\<table\>.*?\<\/table\>', subjects_file_txt)
    read_tables = []
    subjects_tables = []
    table_data = []

    for indexTable, table in enumerate(tables_in_file):
        table_read = pd.read_html(table)[0]
        # table_read.to_csv(os.path.join(root_dir, Path('tmp/converted_documents_md_html/curr_table.txt', sep='\t', index=False)))
        read_tables.append(table_read)
        print(table_read)
        if indexTable == 0:
            # First table is a list of subjects
            header = table_read.values[0]
            header_elems = set()
            header = [elem for elem in header if elem not in header_elems and type(elem) == str and (header_elems.add(elem) or True)]
            table_vals = []
            for index, row in enumerate(table_read.values[1:]):
                ord_num = row[0].replace('.', '') if len(row) > 0 else ''
                subj_code = row[1] if len(row) > 1 else ''
                subj_name = row[2] if len(row) > 1 else ''
                sub_type = row[3] if len(row) > 3 else ''
                subj_sem = row[4] if len(row) > 4 else ''
                subj_p = row[5] if len(row) > 5 else ''
                subj_v = row[6] if len(row) > 6 else ''
                subj_done = row[7] if len(row) > 7 else ''
                subj_other = row[8] if len(row) > 8 else ''
                subj_espb = row[9] if len(row) > 9 else ''
                table_vals.append({'index': ord_num, 'code': subj_code, 'name': subj_name, 'type': sub_type, 'sem': subj_sem, 'p': subj_p, 'v': subj_v, 'don': subj_done, 'other': subj_other, 'espb': subj_espb})
            table_data.append({'type': 'subj_list', 'data': table_vals, 'header': header})
            continue
        # Other tables are subjects tables
        subjects_table = extract_subjects_table(subj_table=table_read)
        subjects_tables.append(subjects_table)
