import os
from pathlib import Path
import re
import sys
import ujson as json
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
import PyQt5.QtGui as QtGui

import src.util as util

class PopupDialog(QDialog):
    def __init__(self, message, title="Warning", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.init_ui(message)

    def init_ui(self, message):
        layout = QVBoxLayout()

        label = QLabel(message)
        ok_button = QPushButton("OK")
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(ok_button)
        btn_layout.addStretch()
        ok_button.clicked.connect(self.accept)

        layout.addWidget(label)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

def generate_html(main_win_root_dir, root_dir=''):
    """
    Generates HTML files from the results.
    """
    root_dir = root_dir if root_dir != '' else main_win_root_dir
    print("Generating HTML files...")
    try:
        util.generate_res_html(root_dir=root_dir)
    except Exception as e:
        print(f'Error generating HTML files:\n    {e}')

def generate_prof_html(main_win_root_dir, root_dir=''):
    """
    Generates professors data HTML file.
    """
    root_dir = root_dir if root_dir != '' else main_win_root_dir
    print("Generating professors data HTML file...")
    try:
        util.generate_prof_html(root_dir=root_dir)
    except Exception as e:
        print(f'Error generating professors data HTML file:\n    {e}')

def generate_subjects_html(main_win_root_dir, root_dir=''):
    """
    Generates subjects data HTML file.
    """
    root_dir = root_dir if root_dir != '' else main_win_root_dir
    print("Generating subjects data HTML file...")
    try:
        util.generate_subjects_html(root_dir=root_dir)
    except Exception as e:
        print(f'Error generating subjects data HTML file:\n    {e}')

def load_html_content(viewer_widget, filename, root_dir):
    """
    Loads content from a locally generated HTML file into QTextEdit.

    Args:
        viewer_widget (QWidget):     Viewer widget to load content into.
        filename (str):              Relative path of the file - relative to the tmp directory.
        root_dir (str):              Root directory of the file, absolute path.
    Returns:
        None
    """
    file_path = os.path.join(root_dir if root_dir == '' else root_dir, Path(f"tmp/{filename}"))
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                html_content = file.read()
            viewer_widget.setHtml(html_content)
        elif filename.endswith('.html') and os.path.exists(os.path.join(root_dir if root_dir == '' else root_dir, Path(f"tmp/{filename[:-5]}.json"))):
            with open(os.path.join(root_dir if root_dir == '' else root_dir, Path(f"tmp/{filename[:-5]}.json")), "r", encoding="utf-8") as file:
                html_content = json.load(file)
            viewer_widget.setHtml(f"<pre>{json.dumps(html_content, indent=4, ensure_ascii=False)}</pre>")
        elif filename.endswith('.html') and os.path.exists(os.path.join(root_dir if root_dir == '' else root_dir, Path(f"tmp/{filename.split(os.sep if re.search(re.escape(os.sep), filename) else '/')[-1][:-5]}.json"))):
            with open(os.path.join(root_dir if root_dir == '' else root_dir, Path(f"tmp/{filename.split(os.sep if re.search(re.escape(os.sep), filename) else '/')[-1][:-5]}.json")), "r", encoding="utf-8") as file:
                html_content = json.load(file)
        else:
            viewer_widget.setHtml(f"<h2>No data found</h2><p>{filename} is missing.</p>")
    except Exception as e:
        print(f'Error loading file:\n    {e}')
        viewer_widget.setHtml(f"<h2>Error loading file</h2><p>{filename} is missing.</p>")

def create_icon(icon_name):
    """
    Creates an icon from the given icon name and path.

    Args:
        icon_name (str):     Name of the icon.
    Returns:
        QIcon:    Created icon.
    """
    icon = QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap(os.path.join(os.path.dirname(__file__), Path(f'resources/icons/{icon_name}.png'))), QtGui.QIcon.Normal, QtGui.QIcon.On)
    return icon

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                                           Elements                                            #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                        QLineEdit, QComboBox, QPushButton, QTableView)
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QRegExp
from PyQt5.QtSql import QSqlQueryModel, QSqlQuery, QSqlDatabase

def connect_to_database(db_path, connection_name="default_connection"):
    """
    Middleware function to establish a database connection.

    Args:
        db_path (str): Path to the database file
        connection_name (str): Unique name for the database connection

    Returns:
        bool: True if connection was successful, False otherwise
    """
    # Check if connection with this name already exists
    if connection_name in QSqlDatabase.connectionNames():
        # Remove existing connection
        QSqlDatabase.removeDatabase(connection_name)

    # Create and configure the database connection
    db = QSqlDatabase.addDatabase("QSQLITE", connection_name)
    db.setDatabaseName(db_path)

    # Open the connection and return status
    success = db.open()
    if not success:
        print(f"Failed to connect to database: {db.lastError().text()}")

    return success

class CustomProxyModel(QSortFilterProxyModel):
    """Custom proxy model to filter on multiple columns"""
    def filterAcceptsRow(self, source_row, source_parent):
        if self.filterKeyColumn() == -1:  # "All Columns" is selected
            # Get the filter string
            regexp = self.filterRegExp()

            # Check each column in the row
            for column in range(self.sourceModel().columnCount()):
                # Get the data for this cell
                index = self.sourceModel().index(source_row, column, source_parent)
                if index.isValid():
                    data = self.sourceModel().data(index)
                    if data is not None and regexp.indexIn(str(data)) != -1:
                        return True
            return False
        else:
            # Use the default implementation for filtering a specific column
            return super().filterAcceptsRow(source_row, source_parent)

class DatabaseTableWidget(QWidget):
    def __init__(self, parent=None):
        """
        Widget to display database table with search functionality.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.table_name = None
        self.connection_name = None

        # Set up the UI
        self.init_ui()

    def init_ui(self):
        # Main layout
        layout = QVBoxLayout(self)

        # Search section
        search_layout = QHBoxLayout()

        # Search label
        search_label = QLabel("Search:")
        search_layout.addWidget(search_label)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter search text...")
        self.search_input.textChanged.connect(self.filter_table)
        search_layout.addWidget(self.search_input)

        # Column selector for search
        self.column_combo = QComboBox()
        self.column_combo.addItem("All Columns")  # Default option
        self.column_combo.currentIndexChanged.connect(self.filter_table)
        search_layout.addWidget(self.column_combo)

        # Clear search button
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear_search)
        search_layout.addWidget(clear_button)

        layout.addLayout(search_layout)

        # Table view
        self.table_view = QTableView()
        self.table_view.setSortingEnabled(True)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        layout.addWidget(self.table_view)

        # Initialize the proxy model
        self.proxy_model = CustomProxyModel()  # Use our custom proxy model
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)

        # Create the source model
        self.source_model = QSqlQueryModel()

    def set_table_data(self, db_path, table_name, connection_name="default_connection"):
        """
        Middleware function to connect to a database and load a specific table.

        Args:
            db_path (str): Path to the database file
            table_name (str): Name of the table to display
            connection_name (str): Name for the database connection

        Returns:
            bool: True if data was loaded successfully, False otherwise
        """
        # Store the table and connection information
        self.table_name = table_name
        self.connection_name = connection_name

        # Connect to the database
        connection_success = connect_to_database(db_path, connection_name)
        if not connection_success:
            return False

        # Load the table data
        return self.load_table_data()

    def load_table_data(self):
        """Load data from the specified table into the table view"""
        if not self.table_name or not self.connection_name:
            print("Table name or connection name not set")
            return False

        # Get the database connection
        db = QSqlDatabase.database(self.connection_name)
        if not db.isValid():
            print(f"Invalid database connection: {self.connection_name}")
            return False

        # Create a query using the specific connection
        query = QSqlQuery(db)
        query_success = query.exec_(f"SELECT * FROM {self.table_name}")

        if not query_success:
            print(f"Query error: {query.lastError().text()}")
            return False

        # Set the query to the model
        self.source_model.setQuery(query)

        # Check if query was successful
        if self.source_model.lastError().isValid():
            print(f"Database error: {self.source_model.lastError().text()}")
            return False

        # Populate the column combo box with column names
        self.column_combo.clear()
        self.column_combo.addItem("All Columns")

        for i in range(self.source_model.columnCount()):
            column_name = self.source_model.headerData(i, Qt.Horizontal)
            self.column_combo.addItem(column_name)

        # Set up the proxy model
        self.proxy_model.setSourceModel(self.source_model)

        # Set the model for the table view
        self.table_view.setModel(self.proxy_model)

        # Adjust column widths
        self.table_view.resizeColumnsToContents()

        return True

    def filter_table(self):
        """Filter the table based on search text and selected column"""
        search_text = self.search_input.text()

        # Get the selected column index (0 means "All Columns")
        column_index = self.column_combo.currentIndex() - 1  # -1 because "All Columns" is at index 0

        # Set the filter on the proxy model
        if column_index >= 0:  # Specific column
            self.proxy_model.setFilterKeyColumn(column_index)
        else:  # All columns
            # We need to implement custom filtering for "All Columns"
            self.proxy_model.setFilterKeyColumn(-1)  # -1 means use custom implementation

        # Set the filter pattern
        self.proxy_model.setFilterRegExp(QRegExp(search_text, Qt.CaseInsensitive))

    def clear_search(self):
        """Clear the search input"""
        self.search_input.clear()
        self.column_combo.setCurrentIndex(0)  # Reset to "All Columns"

    def refresh_data(self):
        """Refresh the table data"""
        if self.table_name and self.connection_name:
            self.load_table_data()

    def get_selected_row_data(self):
        """
        Get data from the currently selected row

        Returns:
            dict: Dictionary of column names and values, or None if no selection
        """
        selected_indexes = self.table_view.selectionModel().selectedRows()
        if not selected_indexes:
            return None

        # Get the first selected row
        proxy_index = selected_indexes[0]
        source_index = self.proxy_model.mapToSource(proxy_index)
        source_row = source_index.row()

        # Collect data from all columns
        row_data = {}
        for col in range(self.source_model.columnCount()):
            column_name = self.source_model.headerData(col, Qt.Horizontal)
            value = self.source_model.data(self.source_model.index(source_row, col))
            row_data[column_name] = value

        return row_data
