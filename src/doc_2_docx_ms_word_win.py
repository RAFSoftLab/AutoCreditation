"""
Converts .doc file to .docx file using Microsoft Word.
"""

import os
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

    if sys.platform.startswith('win'):
        try:
            from win32com import client as wc
        except ImportError:
            print('win32com library not found. Installing...')
            os.system('pip install pywin32')
        from win32com import client as wc

    converted_dir_name = os.sep.join(docx_path.split(os.sep)[:-1])
    if not os.path.exists(converted_dir_name):
        os.makedirs(converted_dir_name, exist_ok=True)

    # word = wc.DispatchEx("Word.Application")
    word = wc.Dispatch('word.Application')
    doc = word.Documents.Open(doc_path)
    doc.SaveAs(docx_path,16)  #16 doc2docx
    doc.Close()
    word.Quit()
    return docx_path if docx_path.endswith('.docx') else docx_path + '.docx'