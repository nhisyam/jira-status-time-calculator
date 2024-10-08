# JIRA Status Time Calculator

## Overview

**JIRA Status Time Calculator** is a Python-based tool designed to interact with the JIRA Agile REST API to fetch, process, and analyze sprint data. It retrieves issues from multiple sprints, calculates the duration each ticket spends in selected statuses during normal working hours, and exports the data into a CSV file for further analysis and visualization.

This tool is ideal for project managers, team leads, and developers who want to gain insights into their team's workflow efficiency, identify bottlenecks, and make data-driven decisions to optimize their processes.

## Prerequisites

Before using the **JIRA Status Time Calculator**, ensure you have the following:

1. **JIRA Account with API Access:**
   - Permissions to access the Agile API and view boards and sprints.
2. **API Token:**
   - For JIRA Cloud instances, generate an API token from your Atlassian account.
   - [How to create an API token](https://confluence.atlassian.com/cloud/api-tokens-938839638.html)
3. **Python Environment:**
   - Python 3.x installed on your machine.
   - Recommended Python version: 3.6 or higher.
4. **Required Python Libraries:**
   - `requests`
   - `pytz`
   
   Install them using pip:
   
   ```bash
   pip install requests pytz

## Installation

1. Clone the Repository:

```bash
git clone https://github.com/yourusername/jira-sprint-analyzer.git
cd jira-sprint-analyzer
```

2. (Optional) Create a Virtual Environment:

It is good practice to use a virtual environment to manage dependencies.

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install Dependencies:

```bash
pip install -r requirements.txt
```

If you don't have a requirements.txt, install the necessary libraries directly:

```bash
pip install requests pytz
```

## Configuration

Before running the script, configure the necessary parameters:

1. Open the Python Script:

Open jira_sprint_analyzer.py (or your script's filename) in your preferred code editor.

2. Update Configuration Variables:

Locate the Configuration section at the top of the script and update the following variables:

```python
# Replace with your JIRA instance URL
JIRA_URL = 'https://your-domain.atlassian.net'

# Replace with your JIRA API token and email
USERNAME = os.getenv('JIRA_USERNAME')
API_TOKEN = os.getenv('JIRA_API_TOKEN')

# Board and Sprint Details
BOARD_NAME = 'Your Board Name'  # Replace with your board name
SPRINT_NAMES = ['Sprint 1', 'Sprint 2']  # List of sprint names to analyze

# Output CSV file path
OUTPUT_CSV = 'jira_sprint_issues.csv'

# Timezone configuration
TIMEZONE = 'UTC'  # e.g., 'UTC', 'America/New_York', etc.

# Story Points Field
STORY_POINTS_FIELD = 'customfield_10002'  # Replace with your Story Points field ID or name

# Selected Statuses to Include in Changelog
SELECTED_STATUSES = ['To Do', 'In Progress', 'Done']  # Modify as needed

# Normal Working Hours Configuration
WORKING_DAYS = [0, 1, 2, 3, 4]  # Monday=0, Sunday=6
WORK_START_HOUR = 9   # 9 AM
WORK_END_HOUR = 17    # 5 PM

# Optional: Define Holidays (as a list of dates)
HOLIDAYS = [
    # '2024-12-25',  # Christmas
    # '2024-01-01',  # New Year's Day
    # Add more holidays as needed
]

# Maximum number of sprints to fetch (to prevent infinite loops)
MAX_SPRINTS = 1000
```

3. Environment Variables (Optional but Recommended):

To enhance security, especially regarding sensitive information like API tokens, consider using environment variables instead of hardcoding them.

- Set Environment Variables:

```bash
export JIRA_USERNAME='your-email@example.com'
export JIRA_API_TOKEN='your-api-token'
```

## Usage

1. Ensure Configuration is Correct:
   Verify that all configuration variables are set correctly, including JIRA credentials, board names, sprint names, working hours, and selected statuses.

2. Run the Script:
   Execute the Python script using the terminal:

```bash
python jira_sprint_analyzer.py
```
_If you named your script differently, replace jira_sprint_analyzer.py with your script's filename._

3. Monitor the Output:
   The script will display progress messages in the terminal, indicating which sprint and issue it's processing.

4. Locate the Output CSV:
   After successful execution, the script will generate a CSV file (jira_sprint_issues.csv by default) in the script's directory.
   
