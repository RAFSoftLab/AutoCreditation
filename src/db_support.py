#!/usr/bin/env python3
"""
Module for converting professor and subject JSON data into a SQLite database
and back to JSON format
"""

import json
from pathlib import Path
import sqlite3
import os
from typing import Dict, List, Any, Optional, Tuple


class ProfessorDBConverter:
    """
    Converts professor data from JSON format into a SQLite database with
    proper relational structure.
    """

    def __init__(self, db_path: str = "acreditation.db"):
        """
        Initialize the converter with path to the target database

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def connect(self) -> None:
        """
        Establish connection to the database
        """
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def close(self) -> None:
        """
        Close the database connection
        """
        if self.conn:
            self.conn.commit()
            self.conn.close()
            self.conn = None
            self.cursor = None

    def create_tables(self) -> None:
        """
        Create the necessary database tables
        """
        # Professors table from prof_tables
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS professors_table (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            title TEXT,
            institution TEXT,
            sci_discipline TEXT
        )
        ''')

        # Subjects table with foreign key to professors (renamed to prof_subjects_table)
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS prof_subjects_table (
            id INTEGER PRIMARY KEY,
            subject_index TEXT,
            code TEXT,
            name TEXT NOT NULL,
            type TEXT,
            studies_programme TEXT,
            studies_type TEXT,
            professor_id INTEGER,
            FOREIGN KEY (professor_id) REFERENCES professors_table (id)
        )
        ''')

        # Professors list table from prof_list
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS professors_list_table (
            id INTEGER PRIMARY KEY,
            ord_num TEXT,
            prof_name TEXT NOT NULL,
            prof_title TEXT
        )
        ''')

        # Programme table for storing general programme information
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS programme_table (
            id INTEGER PRIMARY KEY,
            studies_programme TEXT,
            studies_type TEXT
        )
        ''')

        self.conn.commit()

    def insert_professors_list(self, professors_list: List[Dict[str, Any]]) -> None:
        """
        Insert data into professors_list_table

        Args:
            professors_list: List of professor data dictionaries
        """
        for professor in professors_list:
            self.cursor.execute('''
            INSERT INTO professors_list_table (ord_num, prof_name, prof_title)
            VALUES (?, ?, ?)
            ''', (
                professor.get('ord_num', ''),
                professor.get('prof_name', ''),
                professor.get('prof_title', '')
            ))

        self.conn.commit()

    def insert_professors_and_subjects(self, professors_data: List[Dict[str, Any]]) -> None:
        """
        Insert data into professors_table and prof_subjects_table

        Args:
            professors_data: List of professor data dictionaries including subjects
        """
        for professor in professors_data:
            # Insert professor first
            self.cursor.execute('''
            INSERT INTO professors_table (id, name, title, institution, sci_discipline)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                professor.get('table_key', None),
                professor.get('name', ''),
                professor.get('title', ''),
                professor.get('institution', ''),
                professor.get('sci_discipline', '')
            ))

            professor_id = professor.get('table_key')

            # Insert subjects for this professor
            subjects = professor.get('subjects_all', professor.get('subjects', []))
            for subject in subjects:
                self.cursor.execute('''
                INSERT INTO prof_subjects_table
                (subject_index, code, name, type, studies_programme, studies_type, professor_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    subject.get('index', ''),
                    subject.get('code', ''),
                    subject.get('name', ''),
                    subject.get('type', ''),
                    subject.get('studies_programme', ''),
                    subject.get('studies_type', ''),
                    professor_id
                ))

        self.conn.commit()

    def process_json_file(self, json_path: str) -> None:
        """
        Process the entire JSON file and populate the database

        Args:
            json_path: Path to the JSON file containing professor data
        """
        # Read the JSON file
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Process each section
        for section in data:
            if section['type'] == 'prof_list':
                self.insert_professors_list(section['data'])
            elif section['type'] == 'prof_tables':
                self.insert_professors_and_subjects(section['data'])

        print(f"Successfully processed {json_path} and created database at {self.db_path}")

    def convert(self, json_path: str) -> None:
        """
        Main method to convert JSON to database

        Args:
            json_path: Path to the JSON file containing professor data
        """
        try:
            self.connect()
            self.create_tables()
            self.process_json_file(json_path)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.close()


class SubjectDBConverter:
    """
    Converts subject data from JSON format into a SQLite database with
    proper relational structure.
    """

    def __init__(self, db_path: str = "tmp/acreditation.db"):
        """
        Initialize the converter with path to the target database

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def connect(self) -> None:
        """
        Establish connection to the database
        """
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def close(self) -> None:
        """
        Close the database connection
        """
        if self.conn:
            self.conn.commit()
            self.conn.close()
            self.conn = None
            self.cursor = None

    def create_tables(self) -> None:
        """
        Create the necessary database tables for subjects
        """
        # Main subjects table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS subjects_table (
            id INTEGER PRIMARY KEY,
            subject_index TEXT,
            code TEXT,
            name TEXT NOT NULL,
            type TEXT,
            sem TEXT,
            p TEXT,
            v TEXT,
            don TEXT,
            other TEXT,
            espb TEXT,
            professor TEXT,
            subject_status TEXT,
            condition TEXT,
            theory_classes TEXT,
            practical_classes TEXT,
            studies_programme TEXT,
            school TEXT,
            class_points TEXT
        )
        ''')

        self.conn.commit()

    def insert_subjects(self, subj_list: List[Dict[str, Any]], subj_tables: List[Dict[str, Any]]) -> None:
        """
        Insert data into subjects_table by combining data from subj_list and subj_tables

        Args:
            subj_list: List of subject data dictionaries from subj_list
            subj_tables: List of subject data dictionaries from subj_tables
        """
        # Create a lookup dictionary for subj_list items
        subj_list_lookup = {}
        for subject in subj_list:
            subj_list_lookup[subject.get('code', '')] = subject

        # Process subjects from tables list, adding data from subj_list when available
        for subject in subj_tables:
            # Extract code from subject_code (removing brackets)
            code = subject.get('subject_code', '').strip('[]')

            # Find matching subject in subj_list if exists
            subj_list_data = subj_list_lookup.get(code, {})

            # Handle class_points - convert dictionary to JSON string for storage
            class_points = subject.get('class_points', subj_list_data.get('class_points', {}))
            class_points_json = json.dumps(class_points, ensure_ascii=False) if class_points else ''

            # Combine data from both sources
            self.cursor.execute('''
            INSERT INTO subjects_table (
                subject_index, code, name, type, sem, p, v, don, other, espb,
                professor, subject_status, condition, theory_classes, practical_classes,
                studies_programme, school, class_points
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                subj_list_data.get('index', ''),
                code,
                subject.get('subject_name', ''),
                subj_list_data.get('type', ''),
                subj_list_data.get('sem', ''),
                subj_list_data.get('p', ''),
                subj_list_data.get('v', ''),
                subj_list_data.get('don', ''),
                subj_list_data.get('other', ''),
                subject.get('espb', subj_list_data.get('espb', '')),
                subject.get('professor', ''),
                subject.get('subject_status', ''),
                subject.get('condition', ''),
                subject.get('theory_classes', ''),
                subject.get('practical_classes', ''),
                subject.get('studies_programme', ''),
                subject.get('school', ''),
                class_points_json
            ))

        self.conn.commit()

    def process_json_file(self, json_path: str) -> None:
        """
        Process the subjects JSON file and populate the database

        Args:
            json_path: Path to the JSON file containing subject data
        """
        # Read the JSON file
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        subj_list_data = []
        subj_tables_data = []

        # Process each section
        for section in data:
            if section['type'] == 'subj_list':
                subj_list_data = section['data']
            elif section['type'] == 'subj_tables':
                subj_tables_data = section['data']
                if 'data_all' in section and section['data_all']:
                    # Use data_all if available as it may contain more entries
                    subj_tables_data = section['data_all']

        # Insert the combined subject data
        self.insert_subjects(subj_list_data, subj_tables_data)

        print(f"Successfully processed subjects from {json_path} and updated database at {self.db_path}")

    def convert(self, json_path: str) -> None:
        """
        Main method to convert subjects JSON to database

        Args:
            json_path: Path to the JSON file containing subject data
        """
        try:
            self.connect()
            self.create_tables()
            self.process_json_file(json_path)
        except Exception as e:
            print(f"Error processing subjects: {e}")
        finally:
            self.close()


class ResultsDBConverter:
    """
    Converts results data from JSON format into a SQLite database
    """

    def __init__(self, db_path: str = "tmp/acreditation.db"):
        """
        Initialize the converter with path to the target database

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def connect(self) -> None:
        """
        Establish connection to the database
        """
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def close(self) -> None:
        """Close the database connection"""
        if self.conn:
            self.conn.commit()
            self.conn.close()
            self.conn = None
            self.cursor = None

    def create_tables(self) -> None:
        """
        Create the necessary database tables for results data
        """
        # Programme table for storing general programme information
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS programme_table (
            id INTEGER PRIMARY KEY,
            studies_programme TEXT,
            studies_type TEXT
        )
        ''')

        self.conn.commit()

    def insert_programme_info(self, results_data: Dict[str, Any]) -> None:
        """
        Insert programme data into programme_table

        Args:
            results_data: Dictionary containing results data
        """
        self.cursor.execute('''
        INSERT INTO programme_table (studies_programme, studies_type)
        VALUES (?, ?)
        ''', (
            results_data.get('studies_programme', ''),
            results_data.get('studies_type', '')
        ))

        self.conn.commit()

    def process_json_file(self, json_path: str) -> None:
        """
        Process the results JSON file and populate the database

        Args:
            json_path: Path to the JSON file containing results data
        """
        # Read the JSON file
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Insert programme information
        self.insert_programme_info(data)

        print(f"Successfully processed programme info from {json_path} and updated database at {self.db_path}")

    def convert(self, json_path: str) -> None:
        """
        Main method to convert results JSON to database

        Args:
            json_path: Path to the JSON file containing results data
        """
        try:
            self.connect()
            self.create_tables()
            self.process_json_file(json_path)
        except Exception as e:
            print(f"Error processing results: {e}")
        finally:
            self.close()


class ProfessorDBToJSON:
    """
    Converts SQLite database with professor data back to the original JSON format
    """

    def __init__(self, db_path: str = "tmp/acreditation.db"):
        """
        Initialize the converter with path to the source database

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def connect(self) -> None:
        """
        Establish connection to the database
        """
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # This enables column access by name
        self.cursor = self.conn.cursor()

    def close(self) -> None:
        """
        Close the database connection
        """
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def get_professors_list(self) -> List[Dict[str, Any]]:
        """
        Get professors list data from the database

        Returns:
            List of dictionaries containing professor list data
        """
        self.cursor.execute("SELECT * FROM professors_list_table ORDER BY ord_num")
        professors = self.cursor.fetchall()

        # Convert to list of dictionaries
        result = []
        for prof in professors:
            result.append({
                "ord_num": prof["ord_num"],
                "prof_name": prof["prof_name"],
                "prof_title": prof["prof_title"]
            })

        return result

    def get_professors_table_data(self) -> List[Dict[str, Any]]:
        """
        Get professors table data with their subjects from the database

        Returns:
            List of dictionaries containing professor data with subjects
        """
        # Get all professors
        self.cursor.execute("SELECT * FROM professors_table")
        professors = self.cursor.fetchall()

        result = []
        for prof in professors:
            prof_id = prof["id"]
            prof_data = {
                "table_key": prof_id,
                "name": prof["name"],
                "title": prof["title"],
                "institution": prof["institution"],
                "sci_discipline": prof["sci_discipline"]
            }

            # Get subjects for this professor
            self.cursor.execute("""
                SELECT * FROM prof_subjects_table
                WHERE professor_id = ?
                ORDER BY subject_index
            """, (prof_id,))

            subjects = self.cursor.fetchall()

            # Convert subjects to list of dictionaries
            subjects_list = []
            for subject in subjects:
                subjects_list.append({
                    "index": subject["subject_index"],
                    "code": subject["code"],
                    "name": subject["name"],
                    "type": subject["type"],
                    "studies_programme": subject["studies_programme"],
                    "studies_type": subject["studies_type"]
                })

            # Add subjects to professor data
            prof_data["subjects"] = subjects_list
            prof_data["subjects_all"] = subjects_list.copy()

            # Add to result
            result.append(prof_data)

        return result

    def get_subjects_list_data(self) -> List[Dict[str, Any]]:
        """
        Get subjects list data from the database for subj_list

        Returns:
            List of dictionaries containing subject list data
        """
        self.cursor.execute("""
            SELECT subject_index as "index", code, name, type, sem, p, v, don, other, espb, class_points
            FROM subjects_table
            ORDER BY subject_index
        """)
        subjects = self.cursor.fetchall()

        # Convert to list of dictionaries
        result = []
        for subj in subjects:
            # Parse class_points JSON string back to dictionary
            class_points = {}
            if subj["class_points"]:
                try:
                    class_points = json.loads(subj["class_points"])
                except json.JSONDecodeError:
                    class_points = {}

            result.append({
                "index": subj["index"],
                "code": subj["code"],
                "name": subj["name"],
                "type": subj["type"],
                "sem": subj["sem"],
                "p": subj["p"],
                "v": subj["v"],
                "don": subj["don"],
                "other": subj["other"],
                "espb": subj["espb"],
                "class_points": class_points
            })

        return result

    def get_subjects_table_data(self) -> List[Dict[str, Any]]:
        """
        Get subjects table data from the database for subj_tables

        Returns:
            List of dictionaries containing detailed subject data
        """
        self.cursor.execute("""
            SELECT * FROM subjects_table
            ORDER BY subject_index
        """)
        subjects = self.cursor.fetchall()

        # Convert to list of dictionaries
        result = []
        for subj in subjects:
            # Format the subject code with brackets
            subject_code = f"[{subj['code']}]" if subj['code'] else ""

            # Create the full subject name with code
            subject_full = f"{subject_code} {subj['name']}" if subject_code else subj['name']

            # Parse class_points JSON string back to dictionary
            class_points = {}
            if subj["class_points"]:
                try:
                    class_points = json.loads(subj["class_points"])
                except json.JSONDecodeError:
                    class_points = {}

            result.append({
                "school": subj["school"],
                "studies_programme": subj["studies_programme"],
                "subject": subject_full,
                "subject_code": subject_code,
                "subject_name": subj["name"],
                "professor": subj["professor"],
                "subject_status": subj["subject_status"],
                "espb": subj["espb"],
                "condition": subj["condition"],
                "theory_classes": subj["theory_classes"],
                "practical_classes": subj["practical_classes"],
                "subjects_header": [],
                "class_points": class_points
            })

        return result

    def get_programme_data(self) -> Dict[str, Any]:
        """
        Get programme data from the database

        Returns:
            Dictionary containing programme data
        """
        self.cursor.execute("SELECT studies_programme, studies_type FROM programme_table LIMIT 1")
        programme = self.cursor.fetchone()

        if programme:
            return {
                "studies_programme": programme["studies_programme"],
                "studies_type": programme["studies_type"]
            }
        return {
            "studies_programme": "",
            "studies_type": ""
        }

    def get_headers(self) -> Tuple[List[str], List[str], List[str], List[str]]:
        """
        Get headers for professors list, subjects tables, and subjects lists

        Returns:
            Tuple of (professors_header, subjects_header, subj_list_header, subj_tables_header)
        """
        # Since headers are hardcoded in the original JSON, we'll return them directly
        professors_header = [
            "Red. br.",
            "Matični broj",
            "Prezime, srednje slovo, ime",
            "Zvanje"
        ]

        subjects_header = [
            "R.br.",
            "Oznaka",
            "Naziv predmeta",
            "Vid nastave",
            "Studijski program",
            "Vrsta studija"
        ]

        subj_list_header = [
            "Redni broj",
            "Šifra",
            "Naziv",
            "Uža naučna, umetnička odnosno stručna oblast",
            "Sem.",
            "P",
            "V",
            "DON",
            "Ostali čas.",
            "ESPB"
        ]

        subj_tables_header = []  # Usually empty based on the example

        return professors_header, subjects_header, subj_list_header, subj_tables_header

    def create_professors_json(self) -> List[Dict[str, Any]]:
        """
        Create professors JSON structure from database data

        Returns:
            List with the professors JSON structure
        """
        professors_list = self.get_professors_list()
        professors_tables = self.get_professors_table_data()
        professors_header, subjects_header, _, _ = self.get_headers()

        json_data = [
            {
                "type": "prof_list",
                "data": professors_list,
                "header": professors_header
            },
            {
                "type": "prof_tables",
                "data": professors_tables,
                "header": subjects_header
            }
        ]

        return json_data

    def create_subjects_json(self) -> List[Dict[str, Any]]:
        """
        Create subjects JSON structure from database data

        Returns:
            List with the subjects JSON structure
        """
        subjects_list = self.get_subjects_list_data()
        subjects_tables = self.get_subjects_table_data()
        _, _, subj_list_header, subj_tables_header = self.get_headers()

        json_data = [
            {
                "type": "subj_list",
                "data": subjects_list,
                "header": subj_list_header
            },
            {
                "type": "subj_tables",
                "data": subjects_tables,
                "data_all": subjects_tables,  # Include full data in data_all
                "header": subj_tables_header
            }
        ]

        return json_data

    def create_results_json(self) -> Dict[str, Any]:
        """
        Create results JSON structure from database data

        Returns:
            Dictionary with the results JSON structure
        """
        programme_data = self.get_programme_data()

        # Create basic results structure with programme data
        results_data = {
            "studies_programme": programme_data["studies_programme"],
            "studies_type": programme_data["studies_type"],
            "unmatched_hyperlinks": [],
            "prof_to_subj_not_found": [],
            "subj_to_prof_not_found": [],
            "filtered_results": {
                "studies_programme": programme_data["studies_programme"],
                "prof_to_subj_filt_not_found": [],
                "prof_to_subj_filt_pot_matches_prof_name": [],
                "subj_to_prof_filt_pot_matches_prof_name": [],
                "subj_to_prof_filt_pot_matches_prof_name_middle": [],
                "subj_to_prof_filt_pot_matches_subj_name": []
            }
        }

        return results_data

    def convert_to_json(self, professors_output_path: str, subjects_output_path: str = None, results_output_path: str = None) -> None:
        """
        Convert database to JSON and save to file(s)

        Args:
            professors_output_path: Path to save the professors output JSON file
            subjects_output_path: Path to save the subjects output JSON file (optional)
            results_output_path: Path to save the results output JSON file (optional)
        """
        try:
            self.connect()

            # Process professors data
            professors_json_data = self.create_professors_json()
            if not os.path.exists(os.path.dirname(professors_output_path)):
                os.makedirs(os.path.dirname(professors_output_path), exist_ok=True)
            with open(professors_output_path, 'w', encoding='utf-8') as f:
                json.dump(professors_json_data, f, ensure_ascii=False, indent=4)
            print(f"Successfully converted professors data to JSON file: {professors_output_path}")

            # Process subjects data if path provided
            if subjects_output_path:
                subjects_json_data = self.create_subjects_json()
                if not os.path.exists(os.path.dirname(subjects_output_path)):
                    os.makedirs(os.path.dirname(subjects_output_path), exist_ok=True)
                with open(subjects_output_path, 'w', encoding='utf-8') as f:
                    json.dump(subjects_json_data, f, ensure_ascii=False, indent=4)
                print(f"Successfully converted subjects data to JSON file: {subjects_output_path}")

            # Process results data if path provided
            if results_output_path:
                results_json_data = self.create_results_json()
                if not os.path.exists(os.path.dirname(results_output_path)):
                    os.makedirs(os.path.dirname(results_output_path), exist_ok=True)
                with open(results_output_path, 'w', encoding='utf-8') as f:
                    json.dump(results_json_data, f, ensure_ascii=False, indent=4)
                print(f"Successfully created results data JSON file: {results_output_path}")

        except Exception as e:
            print(f"Error converting database to JSON: {e}")
        finally:
            self.close()


def json_to_db(professors_json_path: str = None, subjects_json_path: str = None,
               results_json_path: str = None, db_path: str = "tmp/acreditation.db") -> None:
    """
    Helper function to convert JSON to database

    Args:
        professors_json_path: Path to the JSON file containing professor data
        subjects_json_path: Path to the JSON file containing subject data
        results_json_path: Path to the JSON file containing results data
        db_path: Path to the SQLite database
    """
    if not os.path.exists(os.path.dirname(db_path)):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    if professors_json_path:
        prof_converter = ProfessorDBConverter(db_path)
        prof_converter.convert(professors_json_path)

    if subjects_json_path:
        subj_converter = SubjectDBConverter(db_path)
        subj_converter.convert(subjects_json_path)

    if results_json_path:
        results_converter = ResultsDBConverter(db_path)
        results_converter.convert(results_json_path)


def db_to_json(db_path: str, professors_output_path: str,
               subjects_output_path: str = None, results_output_path: str = None) -> None:
    """
    Helper function to convert database to JSON

    Args:
        db_path: Path to the SQLite database
        professors_output_path: Path to save the professors output JSON file
        subjects_output_path: Path to save the subjects output JSON file (optional)
        results_output_path: Path to save the results output JSON file (optional)
    """
    if not os.path.exists(os.path.dirname(professors_output_path)):
        os.makedirs(os.path.dirname(professors_output_path), exist_ok=True)
    if not os.path.exists(os.path.dirname(subjects_output_path)):
        os.makedirs(os.path.dirname(subjects_output_path), exist_ok=True)
    if not os.path.exists(os.path.dirname(results_output_path)):
        os.makedirs(os.path.dirname(results_output_path), exist_ok=True)
    converter = ProfessorDBToJSON(db_path)
    converter.convert_to_json(professors_output_path, subjects_output_path, results_output_path)
