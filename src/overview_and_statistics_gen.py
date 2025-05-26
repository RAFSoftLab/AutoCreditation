import json
from collections import Counter, defaultdict
from typing import Dict, List, Any

class AcademicDataAnalyzer:
    """
    A comprehensive analyzer for academic data including professors and subjects.
    Generates professional HTML reports with overview and statistical analysis.
    """

    def __init__(self, prof_data: List[Dict], subj_data: List[Dict]):
        """
        Initialize the analyzer with professor and subject data.

        Args:
            prof_data: List containing professor information
            subj_data: List containing subject information
        """
        self.prof_data = prof_data
        self.subj_data = subj_data
        self._parse_data()

    def _parse_data(self):
        """
        Parse and organize the input data for analysis.
        """
        # Extract professor tables
        self.professors = []
        for item in self.prof_data:
            if item.get('type') == 'prof_tables':
                self.professors.extend(item.get('data', []))

        # Extract subject lists and tables
        self.subjects_list = []
        self.subjects_detail = []

        for item in self.subj_data:
            if item.get('type') == 'subj_list':
                self.subjects_list.extend(item.get('data', []))
            elif item.get('type') == 'subj_tables':
                self.subjects_detail.extend(item.get('data', []))

    def _get_base_styles(self) -> str:
        """
        Return CSS styles for HTML formatting.
        """
        return """
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f8f9fa;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 10px;
                text-align: center;
                margin-bottom: 30px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            .header h1 {
                margin: 0;
                font-size: 2.5em;
                font-weight: 300;
            }
            .header p {
                margin: 10px 0 0 0;
                opacity: 0.9;
                font-size: 1.1em;
            }
            .section {
                background: white;
                margin: 20px 0;
                padding: 25px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .section h2 {
                color: #4a5568;
                border-bottom: 3px solid #667eea;
                padding-bottom: 10px;
                margin-bottom: 20px;
                font-size: 1.8em;
            }
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }
            .stat-card {
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                color: white;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .stat-card h3 {
                margin: 0 0 10px 0;
                font-size: 2.2em;
                font-weight: bold;
            }
            .stat-card p {
                margin: 0;
                opacity: 0.9;
                font-size: 1.1em;
            }
            .prof-card {
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 20px;
                margin: 15px 0;
                background: #f7fafc;
                transition: transform 0.2s;
            }
            .prof-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            }
            .prof-name {
                color: #2d3748;
                font-size: 1.4em;
                font-weight: bold;
                margin-bottom: 5px;
            }
            .prof-title {
                color: #667eea;
                font-weight: 600;
                margin-bottom: 10px;
            }
            .subject-list {
                margin-top: 15px;
            }
            .subject-item {
                background: white;
                padding: 8px 12px;
                margin: 5px 0;
                border-radius: 4px;
                border-left: 4px solid #667eea;
                font-size: 0.9em;
            }
            .chart-container {
                background: white;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .bar-chart {
                display: flex;
                flex-direction: column;
                gap: 10px;
            }
            .bar-item {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .bar-label {
                min-width: 150px;
                font-weight: 600;
                color: #4a5568;
            }
            .bar {
                height: 25px;
                background: linear-gradient(90deg, #667eea, #764ba2);
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: flex-end;
                padding-right: 10px;
                color: white;
                font-weight: bold;
                min-width: 30px;
            }
            .table-container {
                overflow-x: auto;
                margin: 20px 0;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                background: white;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            th {
                background: #667eea;
                color: white;
                padding: 15px 10px;
                text-align: left;
                font-weight: 600;
            }
            td {
                padding: 12px 10px;
                border-bottom: 1px solid #e2e8f0;
            }
            tr:hover {
                background-color: #f7fafc;
            }
            .highlight {
                background: linear-gradient(120deg, #a8edea 0%, #fed6e3 100%);
                padding: 15px;
                border-radius: 6px;
                margin: 15px 0;
                border-left: 4px solid #667eea;
            }
        </style>
        """

    def generate_overview(self) -> str:
        """
        Generate a comprehensive overview of the documentation data.

        Returns:
            str: HTML formatted overview report
        """
        # Basic statistics
        total_professors = len(self.professors)
        total_subjects_list = len(self.subjects_list)
        total_subject_details = len(self.subjects_detail)

        # Get unique study programs
        study_programs = set()
        for prof in self.professors:
            for subject in prof.get('subjects_all', []):
                programs = subject.get('studies_programme', '').split('Softversko inženjerstvo')
                for prog in programs:
                    if prog.strip():
                        study_programs.add(prog.strip())

        # Professor titles distribution
        titles = [prof.get('title', 'Unknown') for prof in self.professors]
        title_counts = Counter(titles)

        html_content = f"""
        <!DOCTYPE html>
        <html lang="sr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Academic Data Overview</title>
            {self._get_base_styles()}
        </head>
        <body>
            <div class="header">
                <h1>📚 Academic Data Overview</h1>
                <p>Comprehensive analysis of professors and subjects data</p>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <h3>{total_professors}</h3>
                    <p>Total Professors</p>
                </div>
                <div class="stat-card">
                    <h3>{total_subjects_list}</h3>
                    <p>Listed Subjects</p>
                </div>
                <div class="stat-card">
                    <h3>{len(study_programs)}</h3>
                    <p>Study Programs</p>
                </div>
                <div class="stat-card">
                    <h3>{total_subject_details}</h3>
                    <p>Detailed Subjects</p>
                </div>
            </div>

            <div class="section">
                <h2>👨‍🏫 Professor Profiles</h2>
        """

        # Add professor cards
        for prof in self.professors:
            subjects_count = len(prof.get('subjects', []))
            all_subjects_count = len(prof.get('subjects_all', []))

            html_content += f"""
                <div class="prof-card">
                    <div class="prof-name">{prof.get('name', 'Unknown')}</div>
                    <div class="prof-title">{prof.get('title', 'Unknown')} | {prof.get('sci_discipline', 'N/A')}</div>
                    <div><strong>Institution:</strong> {prof.get('institution', 'N/A')}</div>
                    <div class="highlight">
                        <strong>Teaching Load:</strong> {subjects_count} active subjects, {all_subjects_count} total subjects
                    </div>
                    <div class="subject-list">
                        <strong>Current Subjects:</strong>
            """

            for subject in prof.get('subjects', [])[:5]:  # Show first 5 subjects
                html_content += f"""
                        <div class="subject-item">
                            <strong>{subject.get('name', 'Unknown')}</strong> ({subject.get('code', 'N/A')})
                            <br><small>{subject.get('studies_programme', 'N/A')} - {subject.get('type', 'N/A')}</small>
                        </div>
                """

            if len(prof.get('subjects', [])) > 5:
                html_content += f"<div class='subject-item'>... and {len(prof.get('subjects', [])) - 5} more subjects</div>"

            html_content += "</div></div>"

        # Professor titles chart
        html_content += f"""
            </div>

            <div class="section">
                <h2>📊 Professor Titles Distribution</h2>
                <div class="chart-container">
                    <div class="bar-chart">
        """

        max_count = max(title_counts.values()) if title_counts else 1
        for title, count in title_counts.most_common():
            width_percent = (count / max_count) * 100
            html_content += f"""
                        <div class="bar-item">
                            <div class="bar-label">{title}</div>
                            <div class="bar" style="width: {width_percent}%">{count}</div>
                        </div>
            """

        html_content += """
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>📖 Subject Information</h2>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Subject Code</th>
                                <th>Subject Name</th>
                                <th>Type</th>
                                <th>Semester</th>
                                <th>ESPB Credits</th>
                                <th>Classes (P/V)</th>
                            </tr>
                        </thead>
                        <tbody>
        """

        # Add subject rows
        for subject in self.subjects_list[:10]:  # Show first 10 subjects
            html_content += f"""
                            <tr>
                                <td><strong>{subject.get('code', 'N/A')}</strong></td>
                                <td>{subject.get('name', 'Unknown')}</td>
                                <td>{subject.get('type', 'N/A')}</td>
                                <td>{subject.get('sem', 'N/A')}</td>
                                <td><strong>{subject.get('espb', 'N/A')}</strong></td>
                                <td>{subject.get('p', '0')}/{subject.get('v', '0')}</td>
                            </tr>
            """

        if len(self.subjects_list) > 10:
            html_content += f"<tr><td colspan='6' style='text-align: center; font-style: italic;'>... and {len(self.subjects_list) - 10} more subjects</td></tr>"

        html_content += """
                        </tbody>
                    </table>
                </div>
            </div>
        </body>
        </html>
        """

        return html_content

    def generate_statistics(self) -> str:
        """
        Generate detailed statistical analysis of the documentation data.

        Returns:
            str: HTML formatted statistics report
        """
        # Calculate various statistics
        stats = self._calculate_statistics()

        html_content = f"""
        <!DOCTYPE html>
        <html lang="sr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Academic Data Statistics</title>
            {self._get_base_styles()}
        </head>
        <body>
            <div class="header">
                <h1>📈 Academic Statistics</h1>
                <p>Detailed statistical analysis and insights</p>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <h3>{stats['avg_subjects_per_prof']:.1f}</h3>
                    <p>Avg Subjects/Professor</p>
                </div>
                <div class="stat-card">
                    <h3>{stats['total_espb']}</h3>
                    <p>Total ESPB Credits</p>
                </div>
                <div class="stat-card">
                    <h3>{stats['avg_espb']:.1f}</h3>
                    <p>Average ESPB/Subject</p>
                </div>
                <div class="stat-card">
                    <h3>{stats['total_class_hours']}</h3>
                    <p>Total Class Hours</p>
                </div>
            </div>

            <div class="section">
                <h2>📚 Subject Type Distribution</h2>
                <div class="chart-container">
                    <div class="bar-chart">
        """

        # Subject types chart
        max_count = max(stats['subject_types'].values()) if stats['subject_types'] else 1
        for subject_type, count in stats['subject_types'].most_common():
            width_percent = (count / max_count) * 100
            html_content += f"""
                        <div class="bar-item">
                            <div class="bar-label">{subject_type}</div>
                            <div class="bar" style="width: {width_percent}%">{count}</div>
                        </div>
            """

        html_content += """
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>🎓 Study Programs Analysis</h2>
                <div class="chart-container">
                    <div class="bar-chart">
        """

        # Study programs chart
        max_count = max(stats['study_programs'].values()) if stats['study_programs'] else 1
        for program, count in stats['study_programs'].most_common():
            width_percent = (count / max_count) * 100
            html_content += f"""
                        <div class="bar-item">
                            <div class="bar-label">{program[:30]}{'...' if len(program) > 30 else ''}</div>
                            <div class="bar" style="width: {width_percent}%">{count}</div>
                        </div>
            """

        html_content += """
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>⏰ Semester Distribution</h2>
                <div class="chart-container">
                    <div class="bar-chart">
        """

        # Semester distribution chart
        max_count = max(stats['semester_dist'].values()) if stats['semester_dist'] else 1
        for semester, count in sorted(stats['semester_dist'].items()):
            width_percent = (count / max_count) * 100
            html_content += f"""
                        <div class="bar-item">
                            <div class="bar-label">Semester {semester}</div>
                            <div class="bar" style="width: {width_percent}%">{count}</div>
                        </div>
            """

        html_content += f"""
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>🏆 Top Professors by Subject Count</h2>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Rank</th>
                                <th>Professor Name</th>
                                <th>Title</th>
                                <th>Active Subjects</th>
                                <th>Total Subjects</th>
                                <th>Main Discipline</th>
                            </tr>
                        </thead>
                        <tbody>
        """

        # Top professors table
        for i, prof_stat in enumerate(stats['prof_subject_counts'][:10], 1):
            html_content += f"""
                            <tr>
                                <td><strong>#{i}</strong></td>
                                <td>{prof_stat['name']}</td>
                                <td>{prof_stat['title']}</td>
                                <td><strong>{prof_stat['active_subjects']}</strong></td>
                                <td>{prof_stat['total_subjects']}</td>
                                <td>{prof_stat['discipline']}</td>
                            </tr>
            """

        html_content += f"""
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="section">
                <h2>💡 Key Insights</h2>
                <div class="highlight">
                    <h3>📊 Statistical Summary:</h3>
                    <ul>
                        <li><strong>Workload Distribution:</strong> Professors teach an average of {stats['avg_subjects_per_prof']:.1f} subjects each</li>
                        <li><strong>Credit System:</strong> Total curriculum worth {stats['total_espb']} ESPB credits with {stats['avg_espb']:.1f} average per subject</li>
                        <li><strong>Teaching Hours:</strong> {stats['total_class_hours']} total class hours across all subjects</li>
                        <li><strong>Program Diversity:</strong> {len(stats['study_programs'])} different study programs offered</li>
                        <li><strong>Academic Structure:</strong> {len(stats['subject_types'])} different subject types available</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """

        return html_content

    def _calculate_statistics(self) -> Dict[str, Any]:
        """
        Calculate statistics from the data.
        """
        stats = {}

        # Professor statistics
        prof_subject_counts = []
        total_active_subjects = 0
        total_all_subjects = 0

        for prof in self.professors:
            active_count = len(prof.get('subjects', []))
            total_count = len(prof.get('subjects_all', []))
            total_active_subjects += active_count
            total_all_subjects += total_count

            prof_subject_counts.append({
                'name': prof.get('name', 'Unknown'),
                'title': prof.get('title', 'Unknown'),
                'active_subjects': active_count,
                'total_subjects': total_count,
                'discipline': prof.get('sci_discipline', 'N/A')
            })

        # Sort professors by active subject count
        prof_subject_counts.sort(key=lambda x: x['active_subjects'], reverse=True)
        stats['prof_subject_counts'] = prof_subject_counts

        # Average subjects per professor
        stats['avg_subjects_per_prof'] = total_active_subjects / len(self.professors) if self.professors else 0

        # Subject statistics
        total_espb = sum(int(subj.get('espb', 0)) for subj in self.subjects_list if subj.get('espb', '0').isdigit())
        stats['total_espb'] = total_espb
        stats['avg_espb'] = total_espb / len(self.subjects_list) if self.subjects_list else 0

        # Calculate total class hours
        total_hours = 0
        for subj in self.subjects_list:
            p_hours = int(subj.get('p', 0)) if str(subj.get('p', 0)).isdigit() else 0
            v_hours = int(subj.get('v', 0)) if str(subj.get('v', 0)).isdigit() else 0
            total_hours += p_hours + v_hours
        stats['total_class_hours'] = total_hours

        # Subject type distribution
        subject_types = Counter(subj.get('type', 'Unknown') for subj in self.subjects_list)
        stats['subject_types'] = subject_types

        # Study programs distribution
        study_programs = Counter()
        for prof in self.professors:
            for subject in prof.get('subjects_all', []):
                program = subject.get('studies_programme', 'Unknown')
                # Handle combined programs
                if 'inženjerstvo' in program:
                    programs = program.split('inženjerstvo')
                    for prog in programs:
                        if prog.strip():
                            study_programs[prog.strip() + ' inženjerstvo'] += 1
                else:
                    study_programs[program] += 1
        stats['study_programs'] = study_programs

        # Semester distribution
        semester_dist = Counter(subj.get('sem', 'Unknown') for subj in self.subjects_list)
        stats['semester_dist'] = semester_dist

        return stats


# Example usage and helper functions
def load_data_from_json(prof_json_str: str, subj_json_str: str) -> AcademicDataAnalyzer:
    """
    Load data from JSON strings and create analyzer instance.

    Args:
        prof_json_str: JSON string containing professor data
        subj_json_str: JSON string containing subject data

    Returns:
        AcademicDataAnalyzer: Configured analyzer instance
    """
    prof_data = json.loads(prof_json_str)
    subj_data = json.loads(subj_json_str)
    return AcademicDataAnalyzer(prof_data, subj_data)

def save_html_report(html_content: str, filename: str):
    """
    Save HTML content to file.

    Args:
        html_content: HTML string to save
        filename: Output filename
    """
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"Report saved to {filename}")
