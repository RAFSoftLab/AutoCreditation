"""
Run the GUI application.
"""

import os
import sys

import src.gui.gui as gui

# root_dir = os.path.dirname(__file__)
root_dir = os.getcwd()

# sys.path.append(root_dir)

def run(root_dir=root_dir):
    """
    Run the application.
    """
    gui.window(root_dir=root_dir)


if __name__ == "__main__":
    run()