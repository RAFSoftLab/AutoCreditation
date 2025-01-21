"""
Converts .doc file to .docx file using Microsoft Word.
"""

import os
from pathlib import Path
import subprocess
import sys


def doc2docx(doc_path, docx_path):
    """
    Converts .doc file to .docx file using Microsoft Word.

    Args:
        doc_path (str):         Absolute path to the .doc file
        docx_path (str):        Absolute path to the .docx file. .docx extension can be omitted.
    Returns:
        (str):                  Absolute path to the created .docx file
    """

    doc_path = str(doc_path) if type(doc_path) == Path else doc_path
    docx_path = str(docx_path) if type(docx_path) == Path else docx_path
    docx_path = docx_path[:-1] if docx_path[-1] == '.' and not (docx_path.endswith('.docx') or docx_path.endswith('.doc')) else docx_path

    if sys.platform.startswith('win'):
        try:
            from win32com import client as wc
        except ImportError:
            print('win32com library not found. Installing...')
            os.system('pip install pywin32')
        from win32com import client as wc

    converted_file_name = docx_path.split(os.sep)[-1]
    converted_dir_name = os.sep.join(docx_path.split(os.sep)[:-1])
    if not os.path.exists(converted_dir_name):
        os.makedirs(converted_dir_name, exist_ok=True)

    if sys.platform.startswith('win'):
        # word = wc.DispatchEx("Word.Application")
        word = wc.Dispatch('word.Application')
        doc = word.Documents.Open(doc_path)
        doc.SaveAs(docx_path,16)  #16 doc2docx
        doc.Close()
        word.Quit()
        return docx_path if docx_path.endswith('.docx') else docx_path + '.docx'
    elif sys.platform.startswith('linux'):
        subprocess.call(['lowriter', '--convert-to', 'docx', '--outdir', f'{os.sep.join(docx_path.split(os.sep)[:-1])}', doc_path])
        if converted_file_name.replace('.docx', '') != doc_path.split(os.sep)[-1].replace('.doc', ''):
            os.rename(os.path.join(docx_path.split(os.sep)[:-1]), doc_path.split(os.sep)[:-1], docx_path)
        return docx_path if docx_path.endswith('.docx') else docx_path + '.docx'
    else:
        print('Unsupported platform. Please use Windows or Linux.')
        return ''