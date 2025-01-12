import os
from pathlib import Path
import shutil

try:
    import aspose.words as aw
except ImportError:
    print('aspose-words library not found. Installing...')
    os.system('pip install aspose-words')
import aspose.words as aw



def convert_to_odt(root_dir, docx_path, file_name='', processed_dir='/tmp/converted_documents/', clear_dir=False, rename_temp_files=False):
    """
    Uses the aspose-words library to convert .doc and .docx files to .odt files.

    Args:
        root_dir (str):          Root directory of the project, absolute path
        docx_path (str):         Relative path to the docx file from the root directory
        file_name (str):         (Optional) Name of the converted text file (without extension). If not specified, input file name is used. Default is ''
        processed_dir (str):     (Optional) Relative path to the directory where the converted txt files will be saved, from the root directory. Default is '/tmp/converted_documents/'
        clear_dir (str):         (Optional) If True, clears the processed_dir directory before converting. Default is False
        rename_temp_files (str): (Optional) If True, renames the files during conversion. Default is False

    Returns:
        (str):                   Path to the converted file
    """

    # Add '/' to start of paths if it is not present
    # docx_path = '/{}'.format(docx_path) if docx_path[0] != '/' else docx_path
    # processed_dir = '/{}'.format(processed_dir) if processed_dir[0] != '/' else processed_dir
    # Remove '/' from the start of paths if it is present
    docx_path = docx_path[1:] if docx_path[0] in [os.sep, '/'] else docx_path
    docx_path = Path(docx_path)
    processed_dir = processed_dir[1:] if processed_dir[0] in [os.sep, '/'] else processed_dir
    processed_dir = Path(processed_dir)

    # Remove processed_dir and all its contents if it exists if clear_dir is set to True
    if clear_dir == True:
        if os.path.exists(os.path.join(root_dir, processed_dir)):
            os.system('rm -rf {}'.format(os.path.join(root_dir, processed_dir)))
    # Create processed_dir directory
    if not os.path.exists(os.path.join(root_dir, processed_dir)):
        os.makedirs(os.path.join(root_dir, processed_dir), exist_ok=True)

    # Copy docx file to temporary location
    # Rename temporary file if rename_temp_files is set to True
    if rename_temp_files == True:
        tmpFile = os.path.join(root_dir, processed_dir, docx_path.split(os.sep)[-1].replace(' ', '_').replace('(', '_').replace(')', '_').replace('-', '_'))
    else:
        tmpFile = os.path.join(root_dir, processed_dir, docx_path.split(os.sep)[-1])
    shutil.copyfile(os.path.join(root_dir, docx_path), tmpFile)

    # file_ext = f'.{tmpFile.split('.')[-1]}'
    file_ext = '.{}'.format(tmpFile.split('.')[-1])
    # file_name = f'{file_name}{file_ext}' if file_name != '' else tmpFile.replace(file_ext, '.odt')
    file_name = os.path.join(root_dir, processed_dir, f'{file_name}.odt') if file_name != '' else tmpFile.replace(file_ext, '.odt')

    # Convert .doc or .docx file to .odt
    doc = aw.Document(tmpFile)
    doc.save(file_name)

    return tmpFile.replace(file_name)