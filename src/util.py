import os
from pathlib import Path
from itertools import islice
import re

import src.util as util



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
            with open(f'{save_dir}/documentation_tree.txt', 'w') as f:
                f.write(struct_txt)
        except Exception as e:
            print(f'Error saving tree structure to {save_dir}/documentation_tree.txt:\n    {e}')
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

    save_dir = '{}{}'.format(root_dir, '/tmp') if save_dir != '' else ''

    # If formed_tree is not passed, tree is generated for the given dir_path directory and saved as a .txt file in the save_dir directory
    if formed_tree == '':
        formed_tree = tree(dir_path=dir_path, save_dir=save_dir if save_tree == True else '', print_tree=print_tree)
        return formed_tree

    # If formed_tree is passed, and it is not a path to a .txt file, it is assumed to be a tree structure as a string
    if not re.search(r'^{}'.format(re.escape(root_dir)), formed_tree):
        if print_tree == True:
            print(formed_tree)
        return formed_tree

    # If formed_tree is passed, and it is a path to a .txt file, it is opened and printed
    with open(formed_tree, 'r') as f:
        saved_tree = f.read()
        if print_tree == True:
            print(saved_tree)
        return saved_tree

def dir_struct(doc_dir, process_names=False):
    """
    Recursively reads a structure of the given documentation directory.

    Args:
        doc_dir (str):           Absolute path to the directory to be read
        process_names (bool):    If True, special characters are removed from the file/directory names. Default is False
        save_struct (bool):      If True, the structure is saved in a file. Default is True

    Returns:
        dir_struct (dict):       Dictionary representing directory: {'name': <name of the file/directory>, 'processed_name': <name with special characters removed>, 'type': <"file" or "directory">, 'path': <path to file/directory>, 'contents': <for directories only (else empty): list of all files in the directory>}
    """

    name = doc_dir.split('/')[-1]
    type = 'directory' if os.path.isdir(doc_dir) else 'file'
    processed_name = util.process_name(name=name, file=True if type == 'file' else False) if process_names == True else name
    path = doc_dir
    contents = []

    if type == 'file':
        return [{'name': name, 'processed_name': processed_name, 'type': type, 'contents': contents}]
    for dir_item in os.listdir(doc_dir):
        if dir_item == '.DS_Store':
            continue
        if os.path.isfile('{}/{}'.format(doc_dir, dir_item)):
            contents.append({'name': dir_item,
                                    'processed_name': util.process_name(name=dir_item, file=True) if process_names == True else dir_item,
                                    'type': 'file',
                                    'path': '{}/{}'.format(doc_dir, dir_item),
                                    'contents': []})
            continue
        contents.append(dir_struct('{}/{}'.format(doc_dir, dir_item), process_names=process_names))
    return {'name': name, 'processed_name': processed_name, 'type': type, 'path': doc_dir, 'contents': contents}
# TODO: rename files while reading structure, if process_names is True