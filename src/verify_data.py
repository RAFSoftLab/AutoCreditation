"""
Verification of data in the documentation files.
"""
import json
import os
import pandas as pd
from pathlib import Path
import re

import src.util as util
import src.results_save_read as results_save_read


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

def extract_professor_table(prof_table, index_table):
    """
    Extracts professor table data from the given table.

    Args:
        prof_table (array):       Professor table
        index_table (int):        Index of the table in the list of tables - to be used as a key for the data dictionary
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
    return {'table_key': index_table,'name': prof_name, 'title': prof_title, 'institution': institution, 'sci_discipline': sci_discipline, 'subjects': subjects, 'subjects_header': subjects_header}

def extract_subjects_table(subj_table):
    """
    Extracts subjects table data from the given table.

    Args:
        subj_table (array):       Subjects table
    Returns:
        (dict):                   Subjects table data
    """
    school, study_programme, subject, subject_code, subject_name, professor, subject_status, espb, condition, theory_classes, practical_classes = '', '', '', '', '', '', '', '', '', '', ''
    subj_header = []
    for index, row in enumerate(subj_table.values):
        if len(row) < 1:
            continue
        if index == 0 and not re.search(r'školska\s+ustanova', row[0], re.I):
            subj_header = row
            continue
        row_elems = set()
        row = [elem for elem in row if elem not in row_elems and type(elem) == str and (row_elems.add(elem) or True)]
        if school == '' and re.search(r'školska\s+ustanova', row[0], re.I):
            school = row[1].strip() if len(row) > 1 else ''
            if len(row) == 1:
                school = re.findall(r'školska\s+ustanova.+', row[0], re.I)[0].strip()
                school = re.sub(r'školska\s+ustanova\:*\s*', '', school)
            continue
        if study_programme == '' and re.search(r'Studijski\s+program', row[0], re.I):
            study_programme = row[1].strip() if len(row) > 1 else ''
            if len(row) == 1:
                study_programme = re.findall(r'Studijski\s+program.+', row[0], re.I)[0].strip()
                study_programme = re.sub(r'[sS]tudijski\s+program\:*\s*', '', study_programme)
            continue
        if subject == '' and re.search(r'Naziv\s+predmeta', row[0], re.I):
            subject = row[1].strip() if len(row) > 1 else ''
            if len(row) == 1:
                subject = re.findall(r'Naziv\s+predmeta.+', row[0], re.I)[0].strip()
                subject = re.sub(r'[nN]aziv\s+predmeta\:*\s*', '', subject)
            if re.search(r'^\[[0-9A-Z\.]+\]', subject):
                subject_code = re.findall(r'^\[[0-9A-Z\.]+\]', subject)[0]
                subject_name = re.sub(re.escape(subject_code), '', subject).strip()
            continue
        if professor == '' and re.search(r'Nastavnik(?:\/nastavnici)*', row[0], re.I):
            professor = row[1].strip() if len(row) > 1 else ''
            if len(row) == 1:
                professor = re.findall(r'Nastavnik(?:\/nastavnici)*.+', row[0], re.I)[0].strip()
                row_name = re.findall(r'Nastavnik(?:\/nastavnici)*\:*', professor, re.I)[0].strip()
                professor = re.sub(re.escape(row_name), '', professor).strip()
            continue
        if subject_status == '' and re.search(r'Status\s+predmeta', row[0], re.I):
            subject_status = row[1].strip() if len(row) > 1 else ''
            if len(row) == 1:
                subject_status = re.findall(r'Status\s+predmeta.+', row[0], re.I)[0].strip()
                subject_status = re.sub(r'[sS]tatus\s+predmeta\:*\s*', '', subject_status)
            continue
        if espb == '' and re.search(r'ESPB', row[0], re.I):
            espb = row[1].strip() if len(row) > 1 else ''
            if len(row) == 1:
                espb = re.findall(r'ESPB.+', row[0], re.I)[0].strip()
                espb = re.sub(r'[eE][sS][pP][bB]\:*\s*', '', espb)
            continue
        if condition == '' and re.search(r'Uslov', row[0], re.I):
            condition = row[1].strip() if len(row) > 1 else ''
            if len(row) == 1:
                condition = re.findall(r'Uslov.+', row[0], re.I)[0].strip()
                condition = re.sub(r'[uU]slov\:*\s*', '', condition)
            continue
        if theory_classes == '' and practical_classes == '' and re.search(r'Broj\s+časova.+nastave', row[0], re.I):
            theory_classes = [i for i in row[1:] if re.search(r'Teorijska\s+nastava', i, re.I)] if len(row) > 1 else []
            theory_classes = theory_classes[0] if len(theory_classes) > 0 else ''
            practical_classes = [i for i in row[1:] if re.search(r'Praktična\s+nastava', i, re.I)] if len(row) > 1 else []
            practical_classes = practical_classes[0] if len(practical_classes) > 0 else ''
            if len(row) == 1:
                theory_classes = re.findall(r'Teorijska\s+nastava\:*\s*[0-9]+', row[0], re.I)[0].strip()
                practical_classes = re.findall(r'Praktična\s+nastava\:*\s*[0-9]+', row[0], re.I)[0].strip()
            theory_classes = re.sub(r'[tT]eorijska\s+nastava\:*\s*', '', theory_classes)
            practical_classes = re.sub(r'[pP]raktična\s+nastava\:*\s*', '', practical_classes)
            continue
    return {'school': school, 'studies_programme': study_programme, 'subject': subject, 'subject_code': subject_code, 'subject_name': subject_name, 'professor': professor, 'subject_status': subject_status, 'espb': espb, 'condition': condition, 'theory_classes': theory_classes, 'practical_classes': practical_classes, 'subjects_header': subj_header}

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
    # Load extracted data
    data = {}
    if os.path.exists(os.path.join(root_dir, Path('tmp/results/results.json'))):
        data = results_save_read.load_results(root_dir=root_dir)
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
        professor_table = extract_professor_table(prof_table=table_read, index_table=indexTable)
        subjects_filter_programme = []
        if data != {} and ('studies_programme' in data.keys() or 'studies_type' in data.keys()):
            studies_programme = data['studies_programme'] if 'studies_programme' in data.keys() else ''
            studies_type = data['studies_type'] if 'studies_type' in data.keys() else ''
            for subject in professor_table['subjects']:
                if studies_type != '' and re.search(studies_type, subject['studies_type']):
                    subjects_filter_programme.append(subject)
                elif studies_programme != '' and re.search(studies_programme, subject['studies_programme']):
                    subjects_filter_programme.append(subject)
            professor_table['subjects_all'] = professor_table['subjects']
            professor_table['subjects'] = subjects_filter_programme
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
    # Load extracted data
    data = {}
    if os.path.exists(os.path.join(root_dir, Path('tmp/results/results.json'))):
        data = results_save_read.load_results(root_dir=root_dir)
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
    subj_tables_filter_programme = []
    if data != {} and ('studies_programme' in data.keys() or 'studies_type' in data.keys()):
        studies_programme = data['studies_programme'] if 'studies_programme' in data.keys() else ''
        studies_type = data['studies_type'] if 'studies_type' in data.keys() else ''
        for subj_table in subjects_tables:
            s_p = True if studies_programme == '' else False
            s_t = True if studies_type == '' else False
            if s_p == False:
                s_p = True if re.search(studies_programme, subj_table['studies_programme']) else False
            if s_t == False and 'studies_type' in subj_table.keys() or 'studies_programme' in subj_table.keys():
                s_t = True if re.search(studies_type, subj_table['studies_type' if 'studies_type' in subj_table.keys() else 'studies_programme']) else False
            if s_p == True and s_t == True:
                subj_tables_filter_programme.append(subj_table)
    table_data.append({'type': 'subj_tables', 'data': subj_tables_filter_programme, 'data_all': subjects_tables, 'header': subjects_tables[0]['subjects_header'] if len(subjects_tables) > 0 else []})
    # Save found data
    save_path = util.save_data(root_dir=root_dir, data=table_data, save_dir='tmp', data_name='subjects_data')
    print(f'Saved subjects data to {save_path}')
    return table_data, save_path

def compare_prof_and_subj_data(root_dir, prof_data='', subj_data='', prof_data_save_path='', subj_data_save_path=''):
    """
    Compares professors and subjects data. Accepts professors and subjects data or paths to the data files.

    Args:
        root_dir (str):              Root directory of the project, absolute path
        prof_data (dict):            Professors data
        subj_data (dict):            Subjects data
        prof_data_save_path (str):   Path to the professors data file
        subj_data_save_path (str):   Path to the subjects data file
    Returns:
        (dict):                       Comparison results
    """
    professors_to_subjects_not_found = []
    subjects_to_professors_not_found = []
    # Load data if path is passed
    if prof_data == '' and prof_data_save_path != '' and os.path.exists(prof_data_save_path):
        prof_data = util.load_data(root_dir=root_dir, abs_path=prof_data_save_path, data_name='professors_data')
    if subj_data == '' and subj_data_save_path != '' and os.path.exists(subj_data_save_path):
        subj_data = util.load_data(root_dir=root_dir, abs_path=subj_data_save_path, data_name='subjects_data')
    prof_tables = [i['data'] for i in prof_data if i['type'] == 'prof_tables']
    prof_tables = prof_tables[0] if len(prof_tables) > 0 else []
    subj_tables = [i['data'] for i in subj_data if i['type'] == 'subj_tables']
    subj_tables = subj_tables[0] if len(subj_tables) > 0 else []
    # Compare professors to subjects
    for indexProf, prof in enumerate(prof_tables):
        print(f"{'-' * 20}\n{indexProf + 1}/{len(prof_tables)}    Finding subjects for professor {prof['name']}...\n")
        for indexProfSubj, prof_subj in enumerate(prof['subjects']):
            subject_found = False
            pot_subjects = []
            for indexSubj, subj in enumerate(subj_tables):
                if not (prof_subj['code'] == subj['subject_code'] or re.search(re.escape(prof_subj['code']), subj['subject'], re.I)):
                    continue
                if not re.search(re.escape(prof['name']), subj['professor']):
                    pot_subjects.append({'type': 'prof_name_mismatch', 'subject': subj})
                    continue
                if not (re.search(re.escape(prof_subj['subject_name'].lower()),subj['subject_name'].lower()) or re.search(re.escape(subj['subject_name']), prof_subj['subject_name'].lower())):
                    pot_subjects.append({'type': 'subj_name_mismatch', 'subject': subj})
                    continue
                subject_found = True
                break
            if subject_found == False:
                professors_to_subjects_not_found.append({'professor': prof['name'], 'subject': f"[{prof_subj['code']}] {prof_subj['name']}", 'subject_code': prof_subj['code'], 'subject_name': prof_subj['name'], 'studies_programme': prof_subj['studies_programme'], 'potential_matches': pot_subjects})
                print(f"    Subject [{prof_subj['code']}] {prof_subj['name']} not found in subjects file!")
            else:
                print(f"    Subject found in subjects file.")
        print(f"\n{'-' * 20}\n")
    # Compare subjects to professors
    for indexSubj, subj in enumerate(subj_tables):
        print(f"{'-' * 20}\n{indexSubj + 1}/{len(subj_tables)}    Finding professor for subject {subj['subject']}...\n")
        professor_found = False
        professor = ''
        pot_professors = []
        for indexProf, prof in enumerate(prof_tables):
            for indexProfSubj, prof_subj in enumerate(prof['subjects']):
                if not ((subj['subject_code'] != '' and subj['subject_code'] == prof_subj['code']) or re.search(re.escape(prof_subj['code']), subj['subject'], re.I)):
                    continue
                if not re.search(re.escape(prof['name']), subj['professor']):
                    pot_professors.append({'type': 'prof_name_mismatch', 'prof': prof})
                    continue
                if not(re.search(re.escape(prof_subj['subject_name'].lower()),subj['subject_name'].lower()) or re.search(re.escape(subj['subject_name']), prof_subj['subject_name'].lower())):
                    pot_professors.append({'type': 'subj_name_mismatch', 'prof': prof})
                    continue
                professor_found = True
                professor = prof
                break
        if professor_found == False:
            subjects_to_professors_not_found.append({'subject': subj['subject'], 'subject_code': subj['subject_code'], 'subject_name': subj['subject_name'], 'studies_programme': subj['studies_programme'], 'professor': subj['professor'], 'potential_matches': pot_professors})
            print(f"    Professor not found in professors file for subject {subj['subject']}!")
        else:
            print(f"    Professor found: {professor['name']}.")
        print(f"\n{'-' * 20}\n")
    # Save results
    results_save_read.save_results(root_dir=root_dir, results={'prof_to_subj_not_found': professors_to_subjects_not_found, 'subj_to_prof_not_found': subjects_to_professors_not_found})
    return {'prof_to_subj_not_found': professors_to_subjects_not_found, 'subj_to_prof_not_found': subjects_to_professors_not_found}

def filter_sort_results(root_dir):
    """
    Sorts the results dictionary into categories.

    Args:
        root_dir (str):          Root directory of the project, absolute path
    Returns:
        (dict):                  Sorted results dictionary, with items
    """
    results_path = os.path.join(root_dir, Path('tmp/results/results.json'))
    if os.path.exists(results_path) and os.path.isfile(results_path):
        results = results_save_read.load_results(root_dir=root_dir, abs_path=results_path)
    studies_programme = results['studies_programme']
    studies_type = results['studies_type'] if 'studies_type' in results.keys() else ''
    prof_to_subj = results['prof_to_subj_not_found']
    subj_to_prof = results['subj_to_prof_not_found']
    # Filter professors to subjects comparison to find unmatched items for specific studies programme and studies type only
    prof_to_subj_filt_not_found = [i for i in prof_to_subj if i['potential_matches'] == []]
    prof_to_subj_filt_not_found = [i for i in prof_to_subj_filt_not_found if i['studies_programme'].lower() == studies_programme.lower() or\
        re.search(re.escape(studies_programme), i['studies_programme'], re.I) or\
            re.search(re.escape(i['studies_programme']), studies_programme, re.I)]
    if studies_type != '':
        prof_to_subj_filt_not_found = [i for i in prof_to_subj_filt_not_found if ('studies_type' in i.keys() and i['studies_type'].lower == studies_type.lower()) or ('studies_type' not in i.keys() and re.search(re.escape(studies_type), i['studies_programme'], re.I))]
    print(f"Professors to subjects not found: {json.dumps(prof_to_subj_filt_not_found, indent=4)}")
    # Filter professors to subjects comparison results to find items with mismatched professor name
    prof_to_subj_filt_pot_matches_prof_name = [i for i in prof_to_subj if i['potential_matches'] != []]
    prof_to_subj_filt_pot_matches_prof_name = [i for i in prof_to_subj_filt_pot_matches_prof_name if True in [True if j['type'] == 'prof_name_mismatch' else False for j in i['potential_matches']]]
    for indexI in range(len(prof_to_subj_filt_pot_matches_prof_name)):
        prof_to_subj_filt_pot_matches_prof_name[indexI]['potential_matches'] = [j for j in prof_to_subj_filt_pot_matches_prof_name[indexI]['potential_matches'] if j['type'] == 'prof_name_mismatch']
    prof_to_subj_filt_pot_matches_prof_name = [i for i in prof_to_subj_filt_pot_matches_prof_name if i['potential_matches'] != []]
    print(f"Professors to subjects comparison results with mismatched professor name: {json.dumps(prof_to_subj_filt_pot_matches_prof_name, indent=4)}")
    # Filter professors to subjects comparison results to find items with mismatched professor name, excluding middle name
    prof_to_subj_filt_pot_matches_prof_name_middle = []
    for indexI, item in enumerate(prof_to_subj_filt_pot_matches_prof_name):
        prof_name_prof = item['professor'].split(' ')
        if len(prof_name_prof) == 3 and prof_name_prof[1].endswith('.') and len(prof_name_prof[1]) in [2, 3]:
            prof_name_prof = [prof_name_prof[0], prof_name_prof[2]]
        potential_matches = []
        for indexJ, item_subj in enumerate(item['potential_matches']):
            prof_name_subj = item_subj['subject']['professor'].split(' ')
            if len(prof_name_subj) == 3 and prof_name_subj[1].endswith('.') and len(prof_name_subj[1]) in [2, 3]:
                prof_name_subj = [prof_name_subj[0], prof_name_subj[2]]
            prof_to_subj_name = ' '.join(prof_name_subj)
            if True not in [True if re.search(re.escape(name_item), prof_to_subj_name) else False for name_item in prof_name_prof]:
                potential_matches.append(item_subj)
        if potential_matches != []:
            item['potential_matches'] = potential_matches
            prof_to_subj_filt_pot_matches_prof_name_middle.append(item)
    print(f"Professors to subjects comparison results with mismatched professor name, excluding middle name: {json.dumps(prof_to_subj_filt_pot_matches_prof_name_middle, indent=4)}")
    # Filter professors to subjects comparison results to find items with mismatched subject name
    prof_to_subj_filt_pot_matches_subj_name = [i for i in prof_to_subj if i['potential_matches'] != []]
    prof_to_subj_filt_pot_matches_subj_name = [i for i in prof_to_subj_filt_pot_matches_subj_name if True in [True if j['type'] == 'subj_name_mismatch' else False for j in i['potential_matches']]]
    for indexI in range(len(prof_to_subj_filt_pot_matches_subj_name)):
        prof_to_subj_filt_pot_matches_subj_name[indexI]['potential_matches'] = [j for j in prof_to_subj_filt_pot_matches_subj_name[indexI]['potential_matches'] if j['type'] == 'subj_name_mismatch']
    prof_to_subj_filt_pot_matches_subj_name = [i for i in prof_to_subj_filt_pot_matches_subj_name if i['potential_matches'] != []]
    print(f"Professors to subjects comparison results with mismatched subject name: {json.dumps(prof_to_subj_filt_pot_matches_subj_name, indent=4)}")
    # Filter subjects to professors comparison to find unmatched items for specific studies programme and studies type only
    subj_to_prof_filt_not_found = [i for i in subj_to_prof if i['potential_matches'] == []]
    subj_to_prof_filt_not_found = [i for i in subj_to_prof_filt_not_found if i['studies_programme'].lower() == studies_programme.lower() or\
        re.search(re.escape(studies_programme), i['studies_programme'], re.I) or\
            re.search(re.escape(i['studies_programme']), studies_programme, re.I)]
    if studies_type != '':
        subj_to_prof_filt_not_found = [i for i in subj_to_prof_filt_not_found if ('studies_type' in i.keys() and i['studies_type'].lower == studies_type.lower()) or ('studies_type' not in i.keys() and re.search(re.escape(studies_type), i['studies_programme'], re.I))]
    print(f"Subjects to professors not found: {json.dumps(subj_to_prof_filt_not_found, indent=4)}")
    # Filter subjects to professors comparison results to find items with mismatched professor name
    subj_to_prof_filt_pot_matches_prof_name = [i for i in subj_to_prof if i['potential_matches'] != []]
    subj_to_prof_filt_pot_matches_prof_name = [i for i in subj_to_prof_filt_pot_matches_prof_name if True in [True if j['type'] == 'prof_name_mismatch' else False for j in i['potential_matches']]]
    for indexI in range(len(subj_to_prof_filt_pot_matches_prof_name)):
        subj_to_prof_filt_pot_matches_prof_name[indexI]['potential_matches'] = [j for j in subj_to_prof_filt_pot_matches_prof_name[indexI]['potential_matches'] if j['type'] == 'prof_name_mismatch']
    subj_to_prof_filt_pot_matches_prof_name = [i for i in subj_to_prof_filt_pot_matches_prof_name if i['potential_matches'] != []]
    print(f"Subjects to professors comparison results with mismatched professor name: {json.dumps(subj_to_prof_filt_pot_matches_prof_name, indent=4)}")
    # Filter subjects to professors comparison results to find items with mismatched subject name, excluding middle name
    subj_to_prof_filt_pot_matches_prof_name_middle = []
    for indexI, item in enumerate(subj_to_prof_filt_pot_matches_prof_name):
        prof_name_subj = item['professor'].split(' ')
        if len(prof_name_subj) == 3 and prof_name_subj[1].endswith('.') and len(prof_name_subj[1]) in [2, 3]:
            prof_name_subj = [prof_name_subj[0], prof_name_subj[2]]
        potential_matches = []
        for indexJ, item_prof in enumerate(item['potential_matches']):
            prof_name_prof = item_prof['prof']['name'].split(' ')
            if len(prof_name_prof) == 3 and prof_name_prof[1].endswith('.') and len(prof_name_prof[1]) in [2, 3]:
                prof_name_prof = [prof_name_prof[0], prof_name_prof[2]]
            subj_to_prof_name = ' '.join(prof_name_prof)
            if True not in [True if re.search(re.escape(name_item), subj_to_prof_name) else False for name_item in prof_name_subj]:
                potential_matches.append(item_prof)
        if potential_matches != []:
            item['potential_matches'] = potential_matches
            subj_to_prof_filt_pot_matches_prof_name_middle.append(item)
    print(f"Subjects to professors comparison results with mismatched subject name, excluding middle name: {json.dumps(subj_to_prof_filt_pot_matches_prof_name_middle, indent=4)}")
    # Filter subjects to professors comparison results to find items with mismatched subject name
    subj_to_prof_filt_pot_matches_subj_name = [i for i in subj_to_prof if i['potential_matches'] != []]
    subj_to_prof_filt_pot_matches_subj_name = [i for i in subj_to_prof_filt_pot_matches_subj_name if True in [True if j['type'] == 'subj_name_mismatch' else False for j in i['potential_matches']]]
    for indexI in range(len(subj_to_prof_filt_pot_matches_subj_name)):
        subj_to_prof_filt_pot_matches_subj_name[indexI]['potential_matches'] = [j for j in subj_to_prof_filt_pot_matches_subj_name[indexI]['potential_matches'] if j['type'] == 'subj_name_mismatch']
    subj_to_prof_filt_pot_matches_subj_name = [i for i in subj_to_prof_filt_pot_matches_subj_name if i['potential_matches'] != []]
    print(f"Subjects to professors comparison results with mismatched subject name: {json.dumps(subj_to_prof_filt_pot_matches_subj_name, indent=4)}")
    results = {
        'studies_programme': studies_programme,
        'prof_to_subj_filt_not_found': prof_to_subj_filt_not_found,
        'prof_to_subj_filt_pot_matches_prof_name': prof_to_subj_filt_pot_matches_prof_name,
        'prof_to_subj_filt_pot_matches_prof_name_middle': prof_to_subj_filt_pot_matches_prof_name_middle,
        'prof_to_subj_filt_pot_matches_subj_name': prof_to_subj_filt_pot_matches_subj_name,
        'subj_to_prof_filt_not_found': subj_to_prof_filt_not_found,
        'subj_to_prof_filt_pot_matches_prof_name': subj_to_prof_filt_pot_matches_prof_name,
        'subj_to_prof_filt_pot_matches_prof_name_middle': subj_to_prof_filt_pot_matches_prof_name_middle,
        'subj_to_prof_filt_pot_matches_subj_name': subj_to_prof_filt_pot_matches_subj_name,
    }
    # Save results
    save_path = results_save_read.save_results(root_dir=root_dir, results={'filtered_results': results})
    print(f'Saved results to {save_path}')
    return results
