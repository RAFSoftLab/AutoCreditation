"""
Saving result to a file and loading saved results.
"""


import json
import os
from pathlib import Path


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

    old_results = []
    new_results = []

    print(f'Saving results to {os.path.join(root_dir, save_dir, Path("results.json"))}')
    if not os.path.exists(save_dir):
        os.makedirs(save_dir, exist_ok=True)
    else:
        if os.path.exists(os.path.join(save_dir, Path('results.json'))):
           with open(os.path.join(save_dir, Path('results.json')), 'r', encoding='utf-8') as f:
               old_results = json.load(f)
    new_results = (old_results + results) if type(results) == list else (old_results + [results])
    with open(os.path.join(save_dir, Path('results.json')), 'w', encoding='utf-8') as f:
        json.dump(new_results, f, indent=4)

def load_results(root_dir, save_dir=''):
    """
    Loads the results from a file.

    Args:
        root_dir (str):          Root directory of the project, absolute path
        save_dir (str):          Relative path to the directory where the results are saved. If not given, uses 'tmp/results'. (Default '')

    Returns:
        (list):                  List of results
    """

    save_dir = Path(save_dir) if save_dir != '' else Path('tmp/results')
    save_dir = os.path.join(root_dir, save_dir)
    if not os.path.exists(save_dir):
        return []
    with open(Path(save_dir), 'r', encoding='utf-8') as f:
        results = json.load(f)
    return results