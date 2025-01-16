"""
Docx utility functions.
- Find hyperlinks in .docx files using the docx library
"""

from pathlib import Path
from docx import Document
from docx.opc.constants import RELATIONSHIP_TYPE as RT


def get_hyperlinks(docx_path):
    """
    Retrieves hyperlinks from the given .docx file.

    Args:
        docx_path (str):         Absolute path to the .docx file

    Returns:
        (list):                  List of hyperlinks
    """

    docx_path = Path(r'{}'.format(docx_path))

    found_hyperlinks = []

    try:
        doc = Document(docx_path)
    except Exception as e:
        file_ref = open(docx_path, 'rb')
        doc = Document(file_ref)

    for relId, rel in doc.part.rels.items():
        if rel.reltype == RT.HYPERLINK:
            print(f"Found hyperlink: {rel._rId} : {rel._target}")
            found_hyperlinks.append({'rel_id': rel._rId, 'rel_target': rel._target})
    return found_hyperlinks