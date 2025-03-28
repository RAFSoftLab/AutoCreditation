"""
Utility functions.
- Clearing /tmp directory
- Removing special characters from the given name
- Creating a tree structure from a given directory
- Printing and saving tree structure
- Reading directory structure and saving it as a .json file
- Finding main documentation file in the given list of files
- Finding hyperlinks in .md files
- Extracting paths from hyperlinks
- Verifying hyperlinks paths exist
"""

import json
import os
from pathlib import Path
from itertools import islice
import re
import shutil
import sys
import pandas as pd

import src.util as util
import src.cyrillyc_to_latin as cyrillic_to_latin
import src.results_save_read as results_save_read


def install_office_package():
    """
    Installs package for Microsoft Office if running on Windows.

    Args:
        None

    Returns:
        None
    """
    if sys.platform.startswith('win'):
        os.system('pip install pywin32')

def clear_tmp_dir(root_dir):
    """
    Clears the /tmp directory.

    Args:
        root_dir (str):          Root directory of the project, absolute path

    Returns:
        None
    """

    tmp_dir = os.path.join(root_dir, Path('tmp'))
    try:
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
    except Exception as e:
        print(f'Error clearing /tmp directory:\n    {e}')

def process_name(name, file=False, skip_ext=True):
    """
    Removes special characters from the given name.

    Args:
        name (str):         Name to be processed
        file (bool):        (Optional) If True, the name is assumed to be a file name. Used to determine if name contains an extension. Default is False
        skip_ext (bool):    If True, the extension of the file is not processed. Default is True

    Returns:
        (str):              Processed name, with special characters removed
    """

    name = name.replace(' ', '_').replace('(', '_').replace(')', '_').replace('-', '_')
    if skip_ext == False and file == False:
        return re.escape(name)
    if not re.search(r'\..+', name):
        return re.escape(name)
    ext = name.split('.')[-1]
    name = re.sub(r'\.{}$'.format(ext), '', name)
    return '{}.{}'.format(re.escape(name), ext)


def tree(dir_path: Path, level: int=-1, limit_to_directories: bool=False, length_limit: int=1000, save_dir: str='', print_tree=True):
    '''
    Given a directory Path object print a visual tree structure

    Args:
        dir_path (Path):                Path to the directory
        level (int):                    (Optional) Level of the tree structure. Default is -1, which means the entire tree structure will be printed
        limit_to_directories (bool):    (Optional) If True, only directories will be printed. Default is False
        length_limit (int):             (Optional) Maximum number of lines to print. Default is 1000
        save_dir (str):                 (Optional) If not empty, the tree structure will be saved as a .txt file in the given directory. Default is ''
        print_tree (bool):              (Optional) If True, the tree structure is printed while being formed. Default is True

    Returns:
        struct_txt (str):               Tree structure as a string
    '''

    # Tree structure symbols
    space =  '    '
    branch = '│   '
    tee =    '├── '
    last =   '└── '

    struct_txt = ''
    dir_path = Path(dir_path) # accept string coerceable to Path
    files = 0
    directories = 0
    def inner(dir_path: Path, prefix: str='', level=-1):
        nonlocal files, directories
        if not level:
            return # 0, stop iterating
        if limit_to_directories:
            contents = [d for d in dir_path.iterdir() if d.is_dir()]
        else:
            contents = list(dir_path.iterdir())
        pointers = [tee] * (len(contents) - 1) + [last]
        for pointer, path in zip(pointers, contents):
            if path.is_dir():
                yield prefix + pointer + path.name
                directories += 1
                extension = branch if pointer == tee else space
                yield from inner(path, prefix=prefix+extension, level=level-1)
            elif not limit_to_directories:
                yield prefix + pointer + path.name
                files += 1
    if print_tree == True:
        print(dir_path.name)
    struct_txt += f'{dir_path.name}\n'
    iterator = inner(dir_path, level=level)
    for line in islice(iterator, length_limit):
        if print_tree == True:
            print(line)
        struct_txt += f'{line}\n'
    if next(iterator, None):
        print(f'... length_limit, {length_limit}, reached, counted:')
        struct_txt += f'... length_limit, {length_limit}, reached, counted:\n'
    print(f'\n{directories} directories' + (f', {files} files' if files else ''))
    struct_txt += '\n{} directories, {} files\n'.format(directories, files if files else '')
    if save_dir != '':
        try:
            if not os.path.exists(save_dir):
                os.makedirs(save_dir, exist_ok=True)
            with open(os.path.join(save_dir, Path('documentation_tree.txt')), 'w') as f:
                f.write(struct_txt)
        except Exception as e:
            print(f'Error saving tree structure to {os.path.join(save_dir, Path("documentation_tree.txt"))}:\n    {e}')
    return struct_txt

def print_save_tree(root_dir, formed_tree='', dir_path='', save_dir='', print_tree=True, save_tree=True):
    '''
    Prints the tree structure of the given directory. If formed_tree is passed, it is printed; otherwise, the tree structure is formed and then printed.

    Args:
        root_dir (str):         Root directory of the project, absolute path
        formed_tree (str):      (Optional) Formed tree structure as a string, or path to a .txt file containing the tree structure. Default is ''
        dir_path (str):         (Optional) Absolute path to the directory for which the tree structure will be printed. Default is ''
        save_dir (str):         (Optional) Absolute path. If not empty, the tree structure will be saved as a .txt file in the given directory, else it is saved in <root_dir>/tmp. Default is ''
        print_tree (bool):      (Optional) If True, the tree structure is printed. Default is True
        save_tree (bool):       (Optional) If True, the tree structure is saved. Default is True

    Returns:
        (str):                  Formed tree structure as a string
    '''

    save_dir = os.path.join(root_dir, Path('tmp')) if save_dir != '' else save_dir

    # If formed_tree is not passed, tree is generated for the given dir_path directory and saved as a .txt file in the save_dir directory
    if formed_tree == '':
        formed_tree = tree(dir_path=dir_path, save_dir=save_dir if save_tree == True else '', print_tree=print_tree)
        return formed_tree

    # If formed_tree is passed, and it is not a path to a .txt file, it is assumed to be a tree structure as a string
    if not re.search(r'^{}'.format(re.escape(root_dir)), str(formed_tree)):
        if print_tree == True:
            print(formed_tree)
            if save_dir != '':
                try:
                    if not os.path.exists(save_dir):
                        os.makedirs(save_dir, exist_ok=True)
                    with open(os.path.join(save_dir, Path('documentation_tree.txt')), 'w') as f:
                        f.write(formed_tree)
                except Exception as e:
                    print(f'Error saving tree structure to {os.path.join(save_dir, Path("documentation_tree.txt"))}:\n    {e}')
        return formed_tree

    # If formed_tree is passed, and it is a path to a .txt file, it is opened and printed
    with open(formed_tree, 'r') as f:
        saved_tree = f.read()
        if print_tree == True:
            print(saved_tree)
        return saved_tree

def dir_struct(doc_dir, process_names=False, convert_to_latin=False):
    """
    Recursively reads a structure of the given documentation directory.

    Args:
        doc_dir (str):           Absolute path to the directory to be read
        process_names (bool):    If True, special characters are removed from the file/directory names. Default is False
        save_struct (bool):      If True, the structure is saved in a file. Default is True
        convert_to_latin (bool): If True, cyrillic characters of the files/directories are converted to latin characters. Files/directories are renamed accordingly. Default is False

    Returns:
        dir_struct (dict):       Dictionary representing directory: {'name': <name of the file/directory>, 'processed_name': <name with special characters removed>, 'type': <"file" or "directory">, 'path': <path to file/directory>, 'contents': <for directories only (else empty): list of all files in the directory>}
    """

    name = doc_dir.split(os.sep)[-1]
    type = 'directory' if os.path.isdir(doc_dir) else 'file'
    processed_name = util.process_name(name=name, file=True if type == 'file' else False) if process_names == True else name
    orig_name = name
    name = cyrillic_to_latin.cyrillic_to_latin(name) if convert_to_latin == True else name
    path = doc_dir
    contents = []

    if type == 'file':
        return [{'name': name, 'orig_name': orig_name, 'processed_name': processed_name, 'type': type, 'contents': contents}]
    for dir_item in os.listdir(doc_dir):
        if dir_item == '.DS_Store':
            continue
        if os.path.isfile(os.path.join(doc_dir, dir_item)):
            contents.append({'name': dir_item if convert_to_latin == False else cyrillic_to_latin.cyrillic_to_latin(dir_item),
                                    'orig_name': dir_item,
                                    'processed_name': util.process_name(name=dir_item, file=True) if process_names == True else dir_item,
                                    'type': 'file',
                                    'path': os.path.join(doc_dir, dir_item if convert_to_latin == False else cyrillic_to_latin.cyrillic_to_latin(dir_item)),
                                    'contents': []})
            continue
        contents.append(dir_struct(os.path.join(doc_dir, dir_item), process_names=process_names))
    return {'name': name, 'orig_name': orig_name, 'processed_name': processed_name, 'type': type, 'path': doc_dir, 'contents': contents}

def save_data(root_dir, data, save_dir='tmp', data_name='data'):
    """
    Saves the given data to a .json file.

    Args:
        root_dir (str):          Root directory of the project, absolute path
        data (dict):             Data to be saved
        save_dir (str):          Relative path to the directory where the data is saved. (Default 'tmp')
        data_name (str):         Name of the data to be saved. (Default 'data')

    Returns:
        (str):                   Path to the saved data
    """
    save_dir = save_dir[1] if save_dir[0] == os.sep else save_dir
    save_path = os.path.join(root_dir, Path(save_dir), f'{data_name}.json')
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    return save_path

def load_data(root_dir, abs_path='', save_dir='tmp', data_name='data'):
    """
    Loads the data from a .json file. If abs_path is not passed, path is created from root_dir, save_dir and data_name.

    Args:
        root_dir (str):          Root directory of the project, absolute path
        abs_path (str):          Absolute path to the data file. If not passed, path is created from root_dir, save_dir and data_name. (Default '')
        save_dir (str):          Relative path to the directory where the data is saved. (Default 'tmp')
        data_name (str):         Name of the data to be saved. (Default 'data')

    Returns:
        (dict):                   Data
    """

    save_dir = save_dir[1] if save_dir[0] == os.sep else save_dir
    save_path = os.path.join(root_dir, Path(save_dir), f'{data_name}.json') if abs_path == '' else abs_path
    with open(save_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def find_main_doc(docs):
    """
    Finds the main documentation file in the given list of files.

    Args:
        docs (list):    List of files

    Returns:
        (dict):         Main documentation file
    """

    main_doc = {}

    for doc in docs:
        if re.search(r'^Dokumentacija', doc['name']):
            main_doc = doc
            break
        if re.search(r'^Dokumentacija', cyrillic_to_latin.cyrillic_to_latin(doc['name'])):
            main_doc = doc
            break
    return main_doc

def find_studies_programme(root_dir, html_file_lat):
    """
    Finds the name of the studies programme in the given .html file.

    Args:
        root_dir (str):        Root directory of the project, absolute path
        html_file_lat (str):   .html file content or absolute path to a saved converted .html file

    Returns:
        (str):                 Name of the studies programme
    """

    # Read file if path is given
    if os.path.exists(html_file_lat) and os.path.isfile(html_file_lat):
        html_file_lat_txt = ''
        with open(html_file_lat, 'r', encoding='utf-8') as f:
            html_file_lat_txt = html_file_lat.read()
        if html_file_lat_txt != '':
            html_file_lat = html_file_lat_txt
        else:
            raise Exception('File not found or empty')

    studies_programme, studies_type = '', ''
    studies_programme_found = False
    stud_type_found = False
    tables_in_file = re.findall(r'\<table\>.*?\<\/table\>', html_file_lat)
    for table in tables_in_file:
        if studies_programme_found == True and stud_type_found == True:
            break
        if not re.search(r'Naziv\s*(?:studijskog)*\s*programa|Studijski\s*program', table, re.I):
            continue
        table_read = pd.read_html(table)[0]
        print(f"Studies programme table: \n{table_read}")
        for index, row in enumerate(table_read.values):
            if studies_programme_found == True and stud_type_found == True:
                break
            if True not in [True if re.search(r'Naziv\s*(?:studijskog)*\s*programa|Studijski\s*program|Vrsta\s*studija', i, re.I) else False for i in row]:
                continue
            for indexCol, col in enumerate(row):
                if studies_programme_found == False and re.search(r'Naziv\s*(?:studijskog)*\s*programa|Studijski\s*program', col, re.I):
                    if len(row) > indexCol + 1:
                        studies_programme = row[indexCol + 1]
                    else:
                        colName = re.findall(r'Naziv\s*(?:studijskog)*\s*programa|Studijski\s*program', col, re.I)[0]
                        studies_programme = re.sub(re.escape(colName), '', col)
                    studies_programme_found = True
                    break
                elif stud_type_found == False and re.search(r'Vrsta\s*studija', col, re.I):
                    if len(row) > indexCol + 1:
                        studies_type = row[indexCol + 1]
                        if not re.search(r'^[A-Z]$', studies_type) and len(studies_type.split()) > 0:
                            studies_type = ''.join([i[0].upper() for i in studies_type.split()])
                    else:
                        colName = re.findall(r'Vrsta\s*studija', col, re.I)[0]
                        studies_type = re.sub(re.escape(colName), '', col)
                    stud_type_found = True
                    break

    results_save_read.save_results(root_dir=root_dir, results={'studies_programme': studies_programme, 'studies_type': studies_type})
    return {'studies_programme': studies_programme, 'studies_type': studies_type}

def find_link_tags(root_dir, doc_dir, html_file_txt, file_format='md'):
    """
    Finds all link tags in the given .md file.

    Args:
        root_dir (str):        Root directory of the project, absolute path
        doc_dir (str):         Absolute path to the documentation directory
        html_file_txt (str):     .md or .html file content
        file_format (str):     (Optional) File format of the file, either 'md' or 'html'. Default is 'md'

    Returns:
        (list):                List of link

    """

    link_tag_lines = []
    link_tags = []

    if file_format == 'md':
        for line in html_file_txt.split('\n'):
            if re.search(r'\(file\:', line) or re.search(r'\(\.\.\{}'.format(os.sep), line):
                link_tag_lines.append(line)
    else:
        link_tag_lines = re.findall(r'\<p\>.*?\<a href\=.*?\<\/a\>.*?\<\/p\>', html_file_txt)

    # Save link tag lines to a file
    if not os.path.exists(os.path.join(root_dir, Path('tmp'))):
        os.makedirs(os.path.join(root_dir, Path('tmp')))
    with open(os.path.join(root_dir, Path('tmp/link_tags.txt')), 'w', encoding='utf-8') as f:
        f.write('\n'.join(link_tag_lines))

    found_tags = []

    for indexLine, line in enumerate(link_tag_lines):
        all_line_tags = extract_path_from_tag(line, doc_dir=doc_dir)
        if all_line_tags == ['not_file_link']:
            continue
        for tag in all_line_tags:
            found_tags.append(tag)

    # Save found tags to a file
    with open(os.path.join(root_dir, Path('tmp/found_file_links.json')), 'w', encoding='utf-8') as f:
        json.dump(found_tags, f, indent=4)

    return found_tags

def extract_path_from_tag(tag_line, doc_dir='', file_format='html'):
    """
    Extracts the path from the given tag.

    Args:
        tag_line (str):         Tag line to be processed
        doc_dir (str):          (Optional) Absolute path to the documentation directory. Default is ''
        file_format (str):      (Optional) File format of the file, either 'md' or 'html'. Default is 'html'

    Returns:
        (str):                  Path extracted from the tag
    """

    line_tags = []

    # TODO: HTML tags
    tag_abs_path = r'file\:\/\/\/'
    tag_rel_path = r'\.\.\/'
    abs_path = True if re.search(tag_abs_path, tag_line) else False

    if file_format == 'html':
        tag_desc = ''
        # Skipping links to file sections and to webpages
        if re.search(r'\<a href\=\"\#', tag_line) or\
            re.search(r'\<a href\=\"http', tag_line):
            return ['not_file_link']
        # Extract links to files
        line_tag = re.findall(r'\<a href\=\"{}.*?\"\>'.format(tag_abs_path if abs_path == True else tag_rel_path), tag_line)
        line_tag = line_tag[0] if line_tag != [] else ''
        tag_name = tag_line.replace(line_tag, '')
        tag_name = tag_name.replace('<p>', '')
        tag_name_split = tag_name.split('</a>')
        tag_name = tag_name_split[0] if len(tag_name_split) > 0 else re.sub(r'\<\/a\>.*', '', tag_name)
        tag_desc = tag_line.replace(line_tag, '').replace(tag_name, '').replace('</a>', '').replace('<p>', '').replace('</p>', '').strip()
        tag_desc = tag_line if tag_desc == '' else tag_desc
        if tag_name[0] == '<' and re.search(r'^\<.*?\>', tag_name):
            tag_tag = re.findall(r'^\<.*?\>', tag_name)
            tag_tag = tag_tag[0] if tag_tag != [] else ''
            tag_close_tag = re.sub(r'^\<', '</', tag_tag)
            tag_name = tag_name.replace(tag_tag, '').replace(tag_close_tag, '').strip()
        tag_path = ''
        if line_tag != '':
            tag_path = line_tag.replace('<a href=', '').replace('>', '')
            tag_path = tag_path[1:] if tag_path[0] in ["'", '"'] else tag_path
            tag_path = tag_path[:-1] if tag_path[-1] in ["'", '"'] else tag_path
            tag_path = re.sub(tag_abs_path if abs_path == True else tag_rel_path, '', tag_path)
        # Verify path exists
        try:
            from urllib import unquote
        except ImportError:
            from urllib.parse import unquote
        if abs_path == True:
            tag_path = unquote(tag_path)
            if os.path.exists(tag_path):
                print(f'Found link to file: {tag_path}')
            else:
                print(f'Link to file not found: {tag_path}')
            return [{'name': tag_name, 'path': tag_path, 'desc': tag_desc, 'line': tag_line}]
        tag_path = re.sub(r'^{}'.format(tag_rel_path), '', tag_path)
        tag_path = tag_path[1:] if tag_path[0] == os.sep else tag_path
        tag_path = os.path.join(doc_dir, Path(tag_path) if str(doc_dir).split(os.sep)[-1] != str(tag_path).split(os.sep)[0] else Path(os.sep.join(tag_path.split(os.sep)[1:])))
        # Convert to readable path
        tag_path = unquote(tag_path)
        if os.path.exists(tag_path):
            print(f'Found link to file: {tag_path}')
        else:
            print(f'Link to file not found: {tag_path}')
        return [{'name': tag_name, 'desc': tag_desc, 'path': tag_path, 'line': tag_line}]
    # TODO: apply same principal as for HTML files
    if file_format == 'md':
        tag_desc = ''
        all_line_tags = re.findall(r'\[.+\]\(file\:.*?\)(?:\s|$|\_\_|\;|\,)', tag_line)
        all_line_tags_alt = re.findall(r'\[.+\]\(\.\.\{}.*?\)(?:\s|$|\_\_|\;|\,)'.format(os.sep), tag_line)
        alt_line_tags = False
        file_tag = 'file\:'
        if all_line_tags == []:
            all_line_tags = all_line_tags_alt
            alt_line_tags = True
            file_tag = '\.\.\{}'.format(os.sep)
        for tag in all_line_tags:
            # Remove tag brackets
            tag_name = re.findall(r'\[.*?\]', tag)[0]
            tag_name = tag_name[1:] if tag_name[0] == '[' else tag_name
            tag_name = tag_name[:-1] if tag_name[-1] == ']' else tag_name
            while tag_name[0] == '_':
                tag_name = tag_name[1:]
            while tag_name[-1] == '_':
                tag_name = tag_name[:-1]
            tag_name = tag_name.replace('\\', '')
            if re.search(r'\({}.+\.?(pdf|doc|docx)\)'.format(file_tag), tag):
                tag_path = re.findall(r'\({}.+\.(?:pdf|doc|docx)\)'.format(file_tag), tag)[0]
            else:
                tag_path = re.findall(r'\({}.+\)'.format(file_tag), tag)[0]
            tag_path = tag_path[6:] if tag_path[0:6] == '(file:' else tag_path[3:] if tag_path[0:3] == '(..' else tag_path
            tag_path = tag_path[:-1] if tag_path[-1] == ')' else tag_path

            while tag_path[0] == '/':
                tag_path = tag_path[1:]
            # Convert to readable path
            try:
                from urllib import unquote
            except ImportError:
                from urllib.parse import unquote
            tag_path = unquote(tag_path)
            # tag_path = tag_path.replace('nј', 'nj')
            # Exclude any text after the longest path in string
            # Convert to absolute path if relative is given
            if abs_path == False:
                tag_path = os.path.join(doc_dir, Path(tag_path))
            tag_alt_path = ''
            if not os.path.exists(tag_path):
                path_found = False
                path_parent = os.sep.join(tag_path.split(os.sep)[:-1])
                if os.path.exists(path_parent) and os.path.isdir(path_parent):
                    parent_dir_contents = os.listdir(path_parent)
                    file_name = tag_path.split(os.sep)[-1]
                    for item in parent_dir_contents:
                        if file_name == cyrillic_to_latin.cyrillic_to_latin(item):
                            path_found = True
                            break
                if path_found == False:
                    tag_path_new = tag_path
                    while len(tag_path_new) > 0:
                        if os.path.exists(tag_path_new):
                            tag_alt_path = tag_path_new
                            break
                        tag_path_new = tag_path_new[:-1]
            tag_desc = tag_line if tag_desc == '' else tag_desc
            line_tags.append({'name': tag_name, 'path': tag_path, 'desc': tag_desc, 'line': tag_line, 'verified_path': tag_alt_path if tag_alt_path != '' else tag_path})
    return line_tags

def verify_hyperlinks(root_dir, found_hyperlinks):
    """
    Verifies if the files listed in the given list of hyperlinks exist.

    Args:
        root_dir (str):          Root directory of the project, absolute path
        found_hyperlinks (list): List of hyperlinks

    Returns:
        (list):                  List of hyperlinks that do not exist
    """

    unmatched_hyperlinks = []
    for hyperlink in found_hyperlinks:
        hyperlink_verified = False
        # Check if hyperlink path exists
        if os.path.exists(hyperlink['path']):
            hyperlink_verified = True
            continue
        # Check if parent directory of hyperlink path exists, and check files in that directory
        parent_dir = os.sep.join(hyperlink['path'].split(os.sep)[:-1])
        if os.path.exists(parent_dir) and os.path.isdir(parent_dir):
            parent_dir_contents = os.listdir(parent_dir)
            file_name = hyperlink['path'].split(os.sep)[-1]
            for item in parent_dir_contents:
                if file_name == cyrillic_to_latin.cyrillic_to_latin(item):
                    hyperlink_verified = True
                    break
            if hyperlink_verified == True:
                continue
        unmatched_hyperlinks.append(hyperlink)
    results_save_read.save_results(root_dir=root_dir, results={'unmatched_hyperlinks': unmatched_hyperlinks})
    return unmatched_hyperlinks

def update_hyperlinks(root_dir, new_hyperlinks):
    """
    Updates saved hyperlinks (file) with the given list of hyperlinks.

    Args:
        root_dir (str):          Root directory of the project, absolute path
        new_hyperlinks (list):   List of hyperlinks
    Returns:
        None
    """

    if not os.path.exists(os.path.join(root_dir, Path('tmp'))):
        os.makedirs(os.path.join(root_dir, Path('tmp')))
    with open(os.path.join(root_dir, Path('tmp/found_file_links.json')), 'w', encoding='utf-8') as f:
        json.dump(new_hyperlinks, f, indent=4)

def generate_res_html(root_dir=''):
    """
    Generates HTML files from the results.
    """
    # self.root_dir = root_dir if root_dir != '' else self.root_dir
    print("Generating HTML files...")
    if os.path.exists(os.path.join(root_dir, Path('tmp/results/results.json'))):
        results_full = util.load_data(root_dir=root_dir, abs_path=os.path.join(root_dir, Path('tmp/results/results.json')))
        results = results_full['filtered_results'] if 'filtered_results' in results_full.keys() else results_full
        results_html = '<html>\n<head>\n<style>\ntable {\n    border: 1px solid black;\n    border-collapse: collapse;\n}\nth, td {\n    border: 1px solid black;\n    padding: 5px;\n    margin: 0px auto;\n    border-collapse: collapse;\n}\n</style>\n</head>\n<body>\n'
        if 'studies_programme' in results_full.keys():
            results_html += f'<h2>Studies programme</h2><p>{results_full["studies_programme"]}</p>\n'
        if 'studies_type' in results_full.keys():
            results_html += f'<h2>Studies type</h2><p>{results_full["studies_type"]}</p>\n'
        if 'unmatched_hyperlinks' in results_full.keys():
            if len(results_full["unmatched_hyperlinks"]) == 0:
                unmatched_hl = 'All hyperlinks verified'
            else:
                unmatched_hl = ''
                for item in results_full["unmatched_hyperlinks"]:
                    if type(item) == dict and 'path' in item.keys():
                        unmatched_hl += f"<li>{item['path']}</li>"
                    else:
                        unmatched_hl += f"<li>{str(item)}</li>"
                unmatched_hl = f"<ul>{unmatched_hl}</ul>"
            results_html += f'<h2>Unmatched hyperlinks</h2><p>{unmatched_hl}</p>\n'
        if 'prof_to_subj_filt_not_found' in results.keys():
            if len(results["prof_to_subj_filt_not_found"]) == 0:
                prof_to_subj_not_found = 'Subject tables found for all subjects listed in professors file'
            else:
                prof_to_subj_not_found = ''
                for item in results["prof_to_subj_filt_not_found"]:
                    if type(item) == dict:
                        prof_table = f"    <tr>\n{'\n'.join([f'            <th>{i}</th>' for i in item.keys() if i != 'potential_matches'])}\n        </tr>\n"
                        prof_table += f"        <tr>\n{'\n'.join([f"            <td>{item[i]}</td>" for i in item.keys() if i != 'potential_matches'])}\n        </tr>\n"
                        prof_table = f"    <table>\n    {prof_table}\n    </table>\n"
                        if 'potential_matches' in item.keys():
                            if len(item['potential_matches']) == 0:
                                prof_table += '<p>No potential subject matches found.</p>'
                            else:
                                prof_table += '<p>Potential subject matches:</p>'
                                pot_match_table = f"    <tr>\n{'\n'.join([f'            <th>{i}</th>' for j in item['potential_matches'] for i in j.keys() if i != 'potential_matches'])}\n        </tr>\n"
                                pot_match_table += f"        <tr>\n{'\n'.join([f"            <td>{item['potential_matches'][i]}</td>" for i in item['potential_matches'].keys() if i != 'potential_matches'])}\n        </tr>\n"
                                pot_match_table = f"    <table>\n    {pot_match_table}\n    </table>\n"
                                prof_table += f"{pot_match_table}"
                        prof_to_subj_not_found += f"{prof_table}<hr>\n"
                    else:
                        prof_to_subj_not_found += f"{str(item)}<hr>"
                prof_to_subj_not_found = f"{prof_to_subj_not_found}"
            results_html += f'<h2>Professors to subjects not found</h2>\n<div>\n    {prof_to_subj_not_found}\n</div>\n'
        if 'subj_to_prof_filt_not_found' in results.keys():
            if len(results["subj_to_prof_filt_not_found"]) == 0:
                subj_to_prof_filt_not_found = 'Subject tables found for all subjects listed in professors file'
            else:
                subj_to_prof_filt_not_found = ''
                for item in results["subj_to_prof_filt_not_found"]:
                    if type(item) == dict:
                        subj_table = f"    <tr>\n{'\n'.join([f'            <th>{i}</th>' for i in item.keys() if i != 'potential_matches'])}\n        </tr>\n"
                        subj_table += f"        <tr>\n{'\n'.join([f"            <td>{item[i]}</td>" for i in item.keys() if i != 'potential_matches'])}\n        </tr>\n"
                        subj_table = f"    <table>\n    {subj_table}\n    </table>\n"
                        if 'potential_matches' in item.keys():
                            if len(item['potential_matches']) == 0:
                                subj_table += '<p>No potential professor matches found.</p>'
                            else:
                                subj_table += '<p>Potential professor matches:</p>'
                                pot_match_table = f"    <tr>\n{'\n'.join([f'            <th>{i}</th>' for j in item['potential_matches'] for i in j.keys() if i != 'potential_matches'])}\n        </tr>\n"
                                pot_match_table += f"        <tr>\n{'\n'.join([f"            <td>{item['potential_matches'][i]}</td>" for i in item['potential_matches'].keys() if i != 'potential_matches'])}\n        </tr>\n"
                                pot_match_table = f"    <table>\n    {pot_match_table}\n    </table>\n"
                                subj_table += f"{pot_match_table}"
                        subj_to_prof_filt_not_found += f"{subj_table}<hr>\n"
                    else:
                        subj_to_prof_filt_not_found += f"{str(item)}<hr>"
                subj_to_prof_filt_not_found = f"{subj_to_prof_filt_not_found}"
            results_html += f'<h2>Subjects to professors not found</h2>\n<div>\n    {subj_to_prof_filt_not_found}\n</div>\n'

        results_html += '</body></html>'
        with open(os.path.join(root_dir, Path('tmp/results/results.html')), 'w', encoding='utf-8') as f:
            f.write(results_html)
    print("HTML files generated.")

def generate_prof_html(root_dir=''):
    """
    Generates HTML file for professors data.

    Args:
        root_dir (str):          Root directory of the project, absolute path

    Returns:
        None
    """
    print("Generating professors HTML file...")
    if os.path.exists(os.path.join(root_dir, Path('tmp/professors_data.json'))):
        prof_data = util.load_data(root_dir=root_dir, abs_path=os.path.join(root_dir, Path('tmp/professors_data.json')))
        prof_data_html = ''
        for prof_data_item in prof_data:
            if 'type' in prof_data_item.keys() and prof_data_item['type'] == 'prof_list':
                prof_data_html += f'<h2>List of professors</h2>\n'
                prof_list_table = ''
                if 'data' not in prof_data_item.keys():
                    prof_data_html += f'<p>No professors list found.</p>\n'
                else:
                    prof_list_table += f'{8 * " "}<tr>\n{12 * " "}<th>Num</th><th>Professor</th><th>Title<\th>\n</tr>\n'
                    for prof_item in prof_data_item['data']:
                        prof_list_table += f'{8 * " "}<tr>\n{12 * " "}<td>{prof_item["ord_num"] if "ord_num" in prof_item.keys() else ""}</td>\n<td>{prof_item["prof_name"] if "prof_name" in prof_item.keys() else ""}</td>\n<td>{prof_item["prof_title"] if "prof_title" in prof_item.keys() else ""}</td>\n</tr>\n'
                    prof_data_html += f'<table>\n{4 * " "}{prof_list_table}\n</table>\n'
            if 'type' in prof_data_item.keys() and prof_data_item['type'] == 'prof_tables':
                prof_data_html += f'<h2>Professor details table</h2>\n'

                if 'data' not in prof_data_item.keys():
                    prof_data_html += f'<p>No professors tables found.</p>\n'
                else:
                    prof_data_tables = f'{8 * " "}<tr>\n{12 * " "}<th>Professor</th><th>Title</th><th>Institution</th><th>Sci. discipline</th><th>Subjects</th>\n</tr>\n'
                    for prof_item in prof_data_item['data']:
                        prof_data_tables += f'{8 * " "}<tr>\n{12 * " "}<td>{prof_item["name"] if "name" in prof_item.keys() else ""}</td><td>{prof_item["title"] if "title" in prof_item.keys() else ""}</td><td>{prof_item["institution"] if "institution" in prof_item.keys() else ""}</td><td>{prof_item["sci_discipline"] if "sci_discipline" in prof_item.keys() else ""}</td><td><a href="{prof_item["table_key"] if "table_key" in prof_item.keys() else ""}">Subjects</a></td>\n</tr>\n'.format(prof_item['subjects_html_path'] if 'subjects_html_path' in prof_item.keys() else '')
                    prof_data_html += f'<table>\n{4 * " "}{prof_data_tables}\n</table>\n'
        prof_data_html = f'<html>\n<head>\n<style>\ntable {{\n    border: 1px solid black;\n    border-collapse: collapse;\n}}\nth, td {{\n    border: 1px solid black;\n    padding: 5px;\n    margin: 0px auto;\n    border-collapse: collapse;\n}}\n</style>\n</head>\n<body>\n{prof_data_html}\n</body>\n</html>'
        with open(os.path.join(root_dir, Path('tmp/results/professors_data.html')), mode='w', encoding='utf-8') as f:
            f.write(prof_data_html)
    print("Professors HTML file generated.")

def generate_subjects_html(root_dir=''):
    """
    Generates HTML file for subjects data.

    Args:
        root_dir (str):          Root directory of the project, absolute path

    Returns:
        None
    """
    print("Generating subjects HTML file...")
    if os.path.exists(os.path.join(root_dir, Path('tmp/subjects_data.json'))):
        subj_data = util.load_data(root_dir=root_dir, abs_path=os.path.join(root_dir, Path('tmp/subjects_data.json')))
        subj_data_html = ''
        for subj_data_item in subj_data:
            if 'type' in subj_data_item.keys() and subj_data_item['type'] == 'subj_list':
                subj_data_html += f'<h2>List of subjects</h2>\n'
                subj_list_table = ''
                if 'data' not in subj_data_item.keys():
                    subj_data_html += f'<p>No subjects list found.</p>\n'
                else:
                    subj_list_table += f'{8 * " "}<tr>\n{12 * " "}<th>Index</th><th>Subject Code</th><th>Subject Name<\th><th>Subject Type<\th><th>Sem<\th><th>P<\th><th>V<\th><th>Don<\th><th>Other<\th><th>ESPB<\th>\n</tr>\n'
                    for subj_item in subj_data_item['data']:
                        subj_list_table += f'{8 * " "}<tr>\n{12 * " "}<td>{subj_item["index"] if "index" in subj_item.keys() else""}</td>\n\
                                                                        <td>{subj_item["code"] if "code" in subj_item.keys() else ""}</td>\n\
                                                                            <td>{subj_item["name"] if "name" in subj_item.keys() else ""}</td>\n\
                                                                                <td>{subj_item["type"] if "type" in subj_item.keys() else ""}</td>\n\
                                                                                    <td>{subj_item["sem"] if "sem" in subj_item.keys() else ""}</td>\n\
                                                                                        <td>{subj_item["p"] if "p" in subj_item.keys() else ""}</td>\n\
                                                                                            <td>{subj_item["v"] if "v" in subj_item.keys() else ""}</td>\n\
                                                                                                <td>{subj_item["don"] if "don" in subj_item.keys() else ""}</td>\n\
                                                                                                    <td>{subj_item["other"] if "other" in subj_item.keys() else ""}</td>\n\
                                                                                                        <td>{subj_item["espb"] if "espb" in subj_item.keys() else ""}</td>\n</tr>\n'
                    subj_data_html += f'<table>\n{4 * " "}{subj_list_table}\n</table>\n'
            if 'type' in subj_data_item.keys() and subj_data_item['type'] == 'subj_tables':
                subj_data_html += f'<h2>Subject details table</h2>\n'

                if 'data' not in subj_data_item.keys():
                    subj_data_html += f'<p>No subjects tables found.</p>\n'
                else:
                    subj_data_tables = f'{8 * " "}<tr>\n{12 * " "}<th>School</th><th>Studies Programme</th><th>Full Name</th><th>Subject Code</th><th>Subject Name</th><th>Professor</th><th>Subject Status</th><th>ESPB</th><th>Condition</th><th>Theory Classes</th><th>Practical Classes</th>\n</tr>\n'
                    for subj_item in subj_data_item['data']:
                        subj_data_tables += f'{8 * " "}<tr>\n{12 * " "}<td>{subj_item["school"] if "school" in subj_item.keys() else ""}</td>\
                                                                        <td>{subj_item["studies_programme"] if "studies_programme" in subj_item.keys() else ""}</td>\
                                                                            <td>{subj_item["subject"] if "subject" in subj_item.keys() else ""}</td>\
                                                                                <td>{subj_item["subject_code"] if "subject_code" in subj_item.keys() else ""}</td>\
                                                                                    <td>{subj_item["subject_name"] if "subject_name" in subj_item.keys() else ""}</td>\
                                                                                        <td>{subj_item["professor"] if "professor" in subj_item.keys() else ""}</td>\
                                                                                            <td>{subj_item["subject_status"] if "subject_status" in subj_item.keys() else ""}</td>\
                                                                                                <td>{subj_item["espb"] if "espb" in subj_item.keys() else ""}</td>\
                                                                                                    <td>{subj_item["condition"] if "condition" in subj_item.keys() else ""}</td>\
                                                                                                        <td>{subj_item["theory_classes"] if "theory_classes" in subj_item.keys() else ""}</td>\
                                                                                                            <td>{subj_item["practical_classes"] if "practical_classes" in subj_item.keys() else ""}</td>\n</tr>\n</tr>\n'
                    subj_data_html += f'<table>\n{4 * " "}{subj_data_tables}\n</table>\n'
        subj_data_html = f'<html>\n<head>\n<style>\ntable {{\n    border: 1px solid black;\n    border-collapse: collapse;\n}}\nth, td {{\n    border: 1px solid black;\n    padding: 5px;\n    margin: 0px auto;\n    border-collapse: collapse;\n}}\n</style>\n</head>\n<body>\n{subj_data_html}\n</body>\n</html>'
        with open(os.path.join(root_dir, Path('tmp/results/subjects_data.html')), mode='w', encoding='utf-8') as f:
            f.write(subj_data_html)

