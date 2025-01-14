"""
Verification of data in the documentation files.
"""


import re


def find_professors_file(root_dir, links, search_regex=''):
    """
    Finds the professors file in the given list of hyperlinks.

    Args:
        root_dir (str):          Root directory of the project, absolute path
        links (list):            List of hyperlinks
        search_regex (str):      (Optional) Regular expression to search for the professors file. If not passed, 'Knjiga\snastavnika' is used. Default is ''

    Returns:
        (dict):                  Professors file
    """
    professors_file = []

    search_regex = r'Knjiga\snastavnika' if search_regex == '' else search_regex

    for link in links:
        if re.search(r'Knjiga\snastavnika', link['line']):
            professors_file.append(link)

    if len(professors_file) > 1:
        print('Multiple professors files found')
        for prof_file in professors_file:
            if re.search(search_regex, prof_file['path']):
                print(f'Professors file found: {prof_file["path"]}')
                return prof_file

    return professors_file[0] if len(professors_file) > 0 else []

def vefify_professors():
    """
    """
    # TODO
    return