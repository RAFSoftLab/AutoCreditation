"""
Saving result to a file and loading saved results.
"""
import json
import os
from pathlib import Path

import src.db_support as db_support


def save_results(root_dir, results):
    """
    Saves the given results to a file.

    Args:
        root_dir (str):          Root directory of the project, absolute path
        results (dict):          Results to be saved

    Returns:
        None
    """
    save_dir = os.path.join(root_dir, Path('tmp/results'))
    old_results = {}
    new_results = {}
    print(f'Saving results to {os.path.join(root_dir, save_dir, Path("results.json"))}')
    if not os.path.exists(save_dir):
        os.makedirs(save_dir, exist_ok=True)
    else:
        if os.path.exists(os.path.join(save_dir, Path('results.json'))):
           with open(os.path.join(save_dir, Path('results.json')), 'r', encoding='utf-8') as f:
               old_results = json.load(f)
    new_results = {**old_results, **results} if old_results != {} else results
    with open(os.path.join(save_dir, Path('results.json')), 'w', encoding='utf-8') as f:
        json.dump(new_results, f, indent=4)
    # Save as database
    db_support.json_to_db(os.path.join(save_dir, Path('professors_data.json')), os.path.join(save_dir, Path('subjects_data.json')), os.path.join(save_dir, Path('acreditation.db')))
    print(f'Saved results to {os.path.join(root_dir, save_dir, Path("results.json"))}')
    print(f'Saved database to {os.path.join(root_dir, save_dir, Path("acreditation.db"))}')

def load_results(root_dir, save_dir='', abs_path=''):
    """
    Loads the results from a file.

    Args:
        root_dir (str):          Root directory of the project, absolute path
        save_dir (str):          Relative path to the directory where the results are saved. If not given, uses 'tmp/results'. (Default '')
        abs_path (str):          Absolute path to the results file. If not given, it is formed with root_dir and save_dir. (Default '')

    Returns:
        (list):                  List of results
    """
    if abs_path == '':
        save_dir = Path(save_dir) if save_dir != '' else Path('tmp/results')
        save_dir = os.path.join(root_dir, save_dir)
        file_path = os.path.join(save_dir, Path('results.json'))
    else:
        file_path = abs_path
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r', encoding='utf-8') as f:
        results = json.load(f)
    return results