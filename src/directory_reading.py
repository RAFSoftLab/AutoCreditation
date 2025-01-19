'''
Directory reading and file listing. Path are saved in a structure.
'''

import json
import os
from pathlib import Path
import shutil
import sys

import src.util as util

is_windows = sys.platform.startswith('win')

def list_dir(root_dir, dir_to_list='', dir_tree='', save_struct=True, convert_to_latin=False):
    """
    Reads structure and creates a tree of the given directory.

    Args:
        root_dir (str):          Root directory of the project, absolute path
        dir_to_list (str):       Absolute path to the directory. If not passed, <root_dir>/tmp/input_files is used. Default is ''
        dir_tree (str):          (Optional) Tree structure representation of the directory. If not passed, it is formed. Default is ''
        save_struct (str):       (Optional) If True, the structure is saved in a file. Default is True
        convert_to_latin (bool): If True, cyrillic characters of the files/directories are converted to latin characters. Files/directories are renamed accordingly. Default is False

    Returns:
        (list):                  List of all files in the directory
        (str):                   Tree structure representation of the directory

    """

    dir_to_list = os.path.join(root_dir, Path('tmp/imput_files')) if dir_to_list == '' else dir_to_list

    dir_struct = []

    # Print and save tree structure of the documentation directory
    dir_tree = util.print_save_tree(root_dir=root_dir, formed_tree=dir_tree, dir_path=dir_to_list, save_dir=os.path.join(root_dir, Path('tmp')), print_tree=False)

    # Read a structure of the documentation directory
    dir_struct = util.dir_struct(doc_dir=dir_to_list, process_names=True, convert_to_latin=convert_to_latin)

    if save_struct == True:
        # Save structure of the documentation directory
        struct_save_dir = os.path.join(root_dir, 'tmp')
        if not os.path.exists(struct_save_dir):
            os.makedirs(struct_save_dir, exist_ok=True)
        try:
            with open(os.path.join(root_dir, Path('tmp/documentation_structure.json')), 'w') as f:
                json.dump(dir_struct, f, indent=4)
        except Exception as e:
            print(f'Error saving structure to {os.path.join(struct_save_dir, Path('documentation_structure.json'))}:\n    {e}')

    return dir_struct, dir_tree

def load_list_dir(root_dir, dir_struct_file='/tmp/documentation_structure.json'):
    """
    Loads structure of the given directory if it was saved in a file.

    Args:
        root_dir (str):          Root directory of the project, absolute path
        dir_struct_file (str):   (Optional) Relative path (from the root directory) to the file containing the structure. Default is '/tmp/documentation_structure.json'

    Returns:
        (dict or None):          Structure of documentation directory
    """

    dir_struct = None

    # Remove '/' from start of path if it is present
    dir_struct_file = dir_struct_file[1:] if dir_struct_file[0] == '/' else dir_struct_file
    dir_struct_file = Path(dir_struct_file)

    if not os.path.exists(os.path.join(root_dir, dir_struct_file)):
        print(f'File {dir_struct_file} does not exist')
        return None
    try:
        with open(os.path.join(root_dir, dir_struct_file), 'r') as f:
            dir_struct = json.load(f)
            print(f'Loaded structure from {dir_struct_file}')
    except Exception as e:
        print(f'Error loading structure from {dir_struct_file}:\n    {e}')

    return dir_struct


def copy_read_doc_dir(root_dir, documentation_dir, working_dir='/tmp/input_files', copy_documentation=True, clear_dir=True, overwrite=True, load_struct=False, convert_names_to_latin=False):
    """
    Copies the given documentation directory to a /tmp directory.

    Args:
        root_dir (str):                     Root directory of the project, absolute path
        documentation_dir (str):            Absolute path to the documentation directory
        working_dir (str):                  (Optional) Relative path (from the root directory) to directory where the copied documentation directory will be saved. Default is '/tmp/input_files
        copy_documentation (str):           (Optional) If True, the documentation directory is copied. Default is True
        clear_dir (str):                    (Optional) If True, clears the working_dir directory before copying. Default is True
        overwrite (str):                    (Optional) If True, overwrites the files in the working_dir directory. Default is True
        load_struct (str):                  (Optional) If True, the structure of the documentation directory is loaded from a file if it exists. Default is False
        convert_names_to_latin (bool):      If True, cyrillic characters of the files/directories are converted to latin characters. Files/directories are renamed accordingly. Default is False

    Returns:
        (list, dict):                       List of all files in the directory, structure of the directory
        (str):                              Tree structure representation of the directory
        (str):                              Absolute path to the working directory (where the copied documentation directory is saved)
    """

    # documentation_dir = r"{}".format(documentation_dir)
    documentation_dir = Path(documentation_dir)

    # Add '/' to start of paths if it is not present
    # working_dir = '/{}'.format(working_dir) if working_dir[0] != '/' else working_dir
    # Remove '/' from start of paths if it is present
    working_dir = working_dir[1:] if working_dir[0] == '/' else working_dir
    working_dir = Path(working_dir)

    doc_dir_path = documentation_dir if copy_documentation == False else os.path.join(root_dir, working_dir)

    # Remove processed_dir and all its contents if it exists if clear_dir is set to True
    if clear_dir == True:
        print(f'Clearing {working_dir}')
        if os.path.exists(os.path.join(root_dir, working_dir)):
            shutil.rmtree(os.path.join(root_dir, working_dir), ignore_errors=True)
    # Create processed_dir directory
    if not os.path.exists(os.path.join(root_dir, working_dir)):
        print(f'Creating {working_dir}')
        os.makedirs(os.path.join(root_dir, working_dir), exist_ok=True)
    # Copy documentation directory contents to working_dir if copy_documentation is set to True
    if copy_documentation == True:
        print(f'Copying files:\n    from {documentation_dir}\n    to {working_dir}')
        shutil.copytree(f'{'\\\\?\\' if is_windows == True else ''}{documentation_dir}', f'{'\\\\?\\' if is_windows == True else ''}{os.path.join(root_dir, working_dir)}', dirs_exist_ok=overwrite, symlinks=True)
        print('Copy complete')
    # Form a tree and structure of the documentation directory
    dir_tree = util.print_save_tree(root_dir=root_dir, dir_path=doc_dir_path)
    # Try to load saved structure of the documentation directory if load_struct is set to True
    dir_struct = None
    if load_struct == True:
        dir_struct = load_list_dir(root_dir=root_dir)
    # Otherwise, form a tree structure of the documentation directory
    if dir_struct == None:
        print('Saved structure of the documentation directory not loaded. Forming a new structure...')
        # Read structure of the documentation directory
        dir_struct, doc_structure_tree = list_dir(root_dir=root_dir, dir_to_list=doc_dir_path, dir_tree=dir_tree, save_struct=True, convert_to_latin=convert_names_to_latin)
    return dir_struct, dir_tree, doc_dir_path
