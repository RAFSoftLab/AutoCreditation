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


# TODO: clean code
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

def find_link_tags(root_dir, doc_dir, md_file_txt, file_format='md'):
    """
    Finds all link tags in the given .md file.

    Args:
        root_dir (str):        Root directory of the project, absolute path
        doc_dir (str):         Absolute path to the documentation directory
        md_file_txt (str):     .md or .html file content
        file_format (str):     (Optional) File format of the file, either 'md' or 'html'. Default is 'md'

    Returns:
        (list):                List of link

    """

    link_tag_lines = []
    link_tags = []

    if file_format == 'md':
        for line in md_file_txt.split('\n'):
            if re.search(r'\(file\:', line) or re.search(r'\(\.\.\{}'.format(os.sep), line):
                link_tag_lines.append(line)
    else:
        link_tag_lines = re.findall(r'\<p\>.*?\<a href\=.*?\<\/a\>.*?\<\/p\>', md_file_txt)

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