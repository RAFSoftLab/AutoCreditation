import os
import mammoth
from markitdown import MarkItDown



def convert_docx_file(root_dir, docx_path, file_name='', processed_dir='/tmp/converted_documents/', clear_dir=False, output_format='html'):
    """
    """

    # Add '/' to start of paths if it is not present
    docx_path = '/{}'.format(docx_path) if docx_path[0] != '/' else docx_path
    processed_dir = '/{}'.format(processed_dir) if processed_dir[0] != '/' else processed_dir

    # Remove processed_dir and all its contents if it exists if clear_dir is set to True
    if clear_dir == True:
        if os.path.exists('{}{}'.format(root_dir, processed_dir)):
            os.system('rm -rf {}'.format('{}{}'.format(root_dir, processed_dir)))
    # Create processed_dir directory
    if not os.path.exists('{}{}'.format(root_dir, processed_dir)):
        os.makedirs('{}{}'.format(root_dir, processed_dir), exist_ok=True)

    file_ext = '.{}'.format('html' if output_format == 'html' else 'md' if output_format == 'md' else 'txt')
    file_name = '{}{}{}{}'.format(root_dir, processed_dir, file_name, file_ext) if file_name != '' else '{}{}{}{}'.format(root_dir, processed_dir, docx_path.split('/')[-1].replace('.docx', '').replace('.doc', ''), file_ext)

    # Convert .docx file to .html
    if output_format == 'html':
        with open('{}{}'.format(root_dir, docx_path), 'rb') as f:
            res = mammoth.convert_to_html(f)
            html = res.value
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(html)
    # Convert .docx file to .md
    if output_format == 'md':
        with open('{}{}'.format(root_dir, docx_path), 'rb') as f:
            res = mammoth.convert_to_markdown(f)
            md = res.value
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(md)
    # Convert .docx file to .txt
    if output_format == 'txt':
        with open('{}{}'.format(root_dir, docx_path), 'rb') as f:
            res = mammoth.extract_raw_text(f)
            txt = res.value
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(txt)

    return file_name


def convert_markitdown(root_dir, docx_path, file_name='', processed_dir='/tmp/converted_documents/', clear_dir=False):
    """
    """

    # Add '/' to start of paths if it is not present
    docx_path = '/{}'.format(docx_path) if docx_path[0] != '/' else docx_path
    processed_dir = '/{}'.format(processed_dir) if processed_dir[0] != '/' else processed_dir

    # Remove processed_dir and all its contents if it exists if clear_dir is set to True
    if clear_dir == True:
        if os.path.exists('{}{}'.format(root_dir, processed_dir)):
            os.system('rm -rf {}'.format('{}{}'.format(root_dir, processed_dir)))
    # Create processed_dir directory
    if not os.path.exists('{}{}'.format(root_dir, processed_dir)):
        os.makedirs('{}{}'.format(root_dir, processed_dir), exist_ok=True)

    file_ext = '.md'
    file_name = '{}{}{}{}'.format(root_dir, processed_dir, file_name, file_ext) if file_name != '' else '{}{}{}{}'.format(root_dir, processed_dir, docx_path.split('/')[-1].replace('.docx', '').replace('.doc', ''), file_ext)


    markitdown = MarkItDown()
    result = markitdown.convert('{}{}'.format(root_dir, docx_path))
    print(result.text_content)

    with open(file_name, 'w', encoding='utf-8') as f:
        f.write(result.text_content)

    return file_name
