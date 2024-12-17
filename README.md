# AutoCreditation

Automated reading and checkup of university acreditation documentation files.

# Overview

 - Converts given documentation files to text and verifies content, confirming that needed documents are and all required information is present.

# Configuration and startup

## Setting up the environment

### Automatic dependency installation

  To automatically install the required dependencies for this project, run:

  ```bash
  pip install -r requirements.txt
  ```

### Manual dependency installation

  To manually install the required dependencies, install the following packages. To create a conda environment, use the following command:

  ```bash
  conda create -n <env_name>
  ```

  | _DEPENDENCY_ | _PIP_ | _CONDA_ |
  | :----------: | :---: | :-----: |
  | docx | pip install python-docx | conda install conda-forge::python-docx |
  | doc2docx | pip install doc2docx | :x: | <!-- ??? -->
  <!-- | textract | pip install textract | conda install conda-forge::textract | -->
  <!-- | tabula-py | pip install tabula-py | conda install conda-forge::tabula-py | -->
  <!-- | antiword | pip install antiword | conda install r::r-antiword | -->


## Running the project

  TODO

## Usage

  TODO

# Changelog

  - 0.0.1 - Project created
    - Initial commit: liscence, readme, project structure
    - Conversion from .docx to .txt
    - Conversion from cyrillic characters to latin characters
    - Updated README.md and requirements.txt