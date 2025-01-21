import os
from pathlib import Path
import re
import mammoth




def convert_docx_file(root_dir, docx_path, file_name='', processed_dir='tmp/converted_documents_md_html/', clear_dir=False, output_format='html'):
    """
    Converts .docx file to .html or .md or .txt file.

    Args:
        root_dir (str):          Root directory of the project, absolute path
        docx_path (str):         Absolute or relative (from the root directory) path to the .docx file
        file_name (str):         Name of the converted text file (without extension). If not specified, input file name is used. Default is ''
        processed_dir (str):     (Optional) Relative path to the directory where the converted txt files will be saved, from the root directory. Default is 'tmp/converted_documents_md_html/'
        clear_dir (str):         (Optional) If True, clears the processed_dir directory before converting. Default is False
        output_format (str):     (Optional) Output format of the converted file. Options are 'html', 'md', 'txt'. Default is 'html'

    Returns:
        (str):                   Path to the converted file
    """

    # Add '/' to start of paths if it is not present
    # docx_path = '/{}'.format(docx_path) if docx_path[0] != '/' else docx_path
    # processed_dir = '/{}'.format(processed_dir) if processed_dir[0] != '/' else processed_dir
    # Remove '/' from the start of paths if it is present
    # if type(docx_path) == str:
    #     docx_path = docx_path[1:] if docx_path[0] in [os.sep, '/'] else docx_path
    #     docx_path = Path(docx_path)
    if type(processed_dir) == str:
        processed_dir = processed_dir[1:] if processed_dir[0] in [os.sep, '/'] else processed_dir
        processed_dir = Path(processed_dir)

    # Remove processed_dir and all its contents if it exists if clear_dir is set to True
    if clear_dir == True:
        if os.path.exists(os.path.join(root_dir, processed_dir)):
            os.system('rm -rf {}'.format(os.path.join(root_dir, processed_dir)))
    # Create processed_dir directory
    if not os.path.exists(os.path.join(root_dir, processed_dir)):
        os.makedirs(os.path.join(root_dir, processed_dir), exist_ok=True)

    file_ext = '.{}'.format('html' if output_format == 'html' else 'md' if output_format == 'md' else 'txt')
    file_name = os.path.join(root_dir, processed_dir, f"{file_name}{file_ext}") if file_name != '' else os.path.join(root_dir, processed_dir, docx_path.split(os.sep)[-1].replace('.docx', '').replace('.doc', ''), file_ext)
    file_path = docx_path if os.path.exists(docx_path) else os.path.join(root_dir, docx_path)

    # Convert .docx file to .html
    if output_format == 'html':
        with open(file_path, 'rb') as f:
            res = mammoth.convert_to_html(f)
            html = res.value
            # remove images
            html = re.sub(r'\<img src\=.*?\>', '', html)
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(html)
    # Convert .docx file to .md
    if output_format == 'md':
        with open(file_path, 'rb') as f:
            res = mammoth.convert_to_markdown(f)
            md = res.value
            # md_no_img = re.sub(r'\_\_\!\[\]\(data\:image*+\)\_\_', '', md)
            md_no_img = ''
            for line in md.split('\n'):
                in_img = False
                last_img_line = False
                if in_img == False and re.search(r'\_\_\!\[\]\(data\:image', line):
                    in_img = True
                    continue
                if in_img == True and re.search(r'\)\_\_', line):
                    last_img_line = True
                    continue
                if last_img_line == True:
                    in_img = False
                    last_img_line = False
                    continue
                md_no_img += line + '\n'
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(md_no_img)
    # Convert .docx file to .txt
    if output_format == 'txt':
        with open(file_path, 'rb') as f:
            res = mammoth.extract_raw_text(f)
            txt = res.value
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(txt)

    return file_name

# Not used
def convert_markitdown(root_dir, docx_path, file_name='', processed_dir='/tmp/converted_documents_md_html', clear_dir=False):
    """
    Converts .docx file to .md file using markitdown library.

    Args:
        root_dir (str):          Root directory of the project, absolute path
        docx_path (str):         Relative path to the docx file from the root directory
        file_name (str):         (Optional) Name of the converted text file (without extension). If not specified, input file name is used. Default is ''
        processed_dir (str):     (Optional) Relative path to the directory where the converted txt files will be saved, from the root directory. Default is '/tmp/converted_documents_md_html/'
        clear_dir (str):         (Optional) If True, clears the processed_dir directory before converting. Default is False

    Returns:
        (str):                   Path to the converted file
    """

    try:
        from markitdown import MarkItDown
    except ImportError:
        print('markitdown library not found. Installing...')
        os.system('pip install markitdown')
    from markitdown import MarkItDown

    # Add '/' to start of paths if it is not present
    # docx_path = '/{}'.format(docx_path) if docx_path[0] != '/' else docx_path
    # processed_dir = '/{}'.format(processed_dir) if processed_dir[0] != '/' else processed_dir
    # Remove '/' from the start of paths if it is present
    docx_path = docx_path[1:] if docx_path[0] in [os.sep, '/'] else docx_path
    docx_path = Path(docx_path)
    processed_dir = processed_dir[1:] if processed_dir[0] in [os.sep, '/'] else processed_dir
    processed_dir = Path(processed_dir)

    file_path = docx_path if os.path.exists(docx_path) else os.path.join(root_dir, docx_path)

    # Remove processed_dir and all its contents if it exists if clear_dir is set to True
    if clear_dir == True:
        if os.path.exists(os.path.join(root_dir, processed_dir)):
            os.system('rm -rf {}'.format(os.path.join(root_dir, processed_dir)))
    # Create processed_dir directory
    if not os.path.exists(os.path.join(root_dir, processed_dir)):
        os.makedirs(os.path.join(root_dir, processed_dir), exist_ok=True)

    file_ext = '.md'
    file_name = os.path.join(root_dir, processed_dir, f"{file_name}{file_ext}") if file_name != '' else os.path.join(root_dir, processed_dir, f"{docx_path.split(os.sep)[-1].replace('.docx', '').replace('.doc', '')}{file_ext}")


    markitdown = MarkItDown()
    result = markitdown.convert(file_path)
    print(result.text_content)

    with open(file_name, 'w', encoding='utf-8') as f:
        f.write(result.text_content)

    return file_name
