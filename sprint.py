import requests
from requests.auth import HTTPBasicAuth
import datetime
import csv
import time as t
import pytz
from datetime import datetime, time, timedelta
import os

# ---------------------------- Configuration ---------------------------- #

# Replace with your JIRA instance URL
JIRA_URL = os.getenv('JIRA_URL')

# Replace with your JIRA API token and email
USERNAME = os.getenv('USERNAME')
API_TOKEN = os.getenv('API_TOKEN')

# Board and Sprint Details
BOARD_NAME = 'MOAR Dev Board'

# Define the list of sprint names you want to process
SPRINT_NAMES = ['MOAR 2024 Sprint 19', 'MOAR 2024 Sprint 18', 'MOAR 2024 Sprint 17', 'MOAR 2024 Sprint 16']  # Modify as needed

# Output CSV file path
OUTPUT_CSV = 'jira_sprint_issues.csv'

# Timezone configuration (optional)
# Example: 'UTC', 'America/New_York', etc.
TIMEZONE = 'Asia/Kuala_Lumpur'

# Maximum number of sprints to fetch (to prevent infinite loops)
MAX_SPRINTS = 1000

# Story Points Field
# Use the exact field name or custom field ID
STORY_POINTS_FIELD = 'customfield_10124' 

# Selected Statuses to Include in Changelog
SELECTED_STATUSES = ['In Progress', 'In Review']  # Modify as needed

# Normal Working Hours Configuration
WORKING_DAYS = [0, 1, 2, 3, 4]  # Monday=0, Sunday=6
WORK_START_HOUR = 9   # 9 AM
WORK_END_HOUR = 18    # 6 PM

# Optional: Define Holidays (as a list of dates)
HOLIDAYS = [
    # '2024-12-25',  # Christmas
    # '2024-01-01',  # New Year's Day
    # Add more holidays as needed
]

# ---------------------------- Helper Functions ---------------------------- #

def calculate_business_hours(start_dt, end_dt, working_days, work_start_hour, work_end_hour, holidays=[]):
    """
    Calculate the total business hours between two datetime objects.

    Args:
        start_dt (datetime): The start datetime.
        end_dt (datetime): The end datetime.
        working_days (list): List of integers representing working days (Monday=0, Sunday=6).
        work_start_hour (int): Start hour of the workday (24-hour format).
        work_end_hour (int): End hour of the workday (24-hour format).
        holidays (list): List of dates (as strings 'YYYY-MM-DD') that are holidays.

    Returns:
        float: Total business hours between start_dt and end_dt.
    """
    if start_dt > end_dt:
        return 0.0

    # Convert holiday strings to date objects
    holiday_dates = set()
    for holiday in holidays:
        try:
            holiday_date = datetime.strptime(holiday, '%Y-%m-%d').date()
            holiday_dates.add(holiday_date)
        except ValueError:
            continue  # Skip invalid date formats

    total_business_seconds = 0

    current_day = start_dt.date()
    end_day = end_dt.date()

    while current_day <= end_day:
        # Check if current day is a working day and not a holiday
        if current_day.weekday() in working_days and current_day not in holiday_dates:
            # Define working period for the current day
            work_start = datetime.combine(current_day, time(hour=work_start_hour, minute=0, second=0, tzinfo=start_dt.tzinfo))
            work_end = datetime.combine(current_day, time(hour=work_end_hour, minute=0, second=0, tzinfo=start_dt.tzinfo))

            # Determine the actual start and end times for calculation
            actual_start = max(start_dt, work_start)
            actual_end = min(end_dt, work_end)

            # Calculate overlap
            if actual_start < actual_end:
                delta = actual_end - actual_start
                total_business_seconds += delta.total_seconds()

        current_day += timedelta(days=1)

    # Convert seconds to hours
    total_business_hours = total_business_seconds / 3600.0
    return total_business_hours

def get_board_id(jira_url, username, api_token, board_name):
    """
    Fetches the Board ID for a given board name.
    
    Args:
        jira_url (str): Base URL of the JIRA instance.
        username (str): JIRA account email.
        api_token (str): API token.
        board_name (str): Name of the board.
        
    Returns:
        int: Board ID if found, else None.
    """
    url = f"{jira_url}/rest/agile/1.0/board"
    auth = HTTPBasicAuth(username, api_token)
    headers = {"Accept": "application/json"}
    params = {"name": board_name, "type": "scrum"}  # Adjust 'type' if needed
    
    response = requests.get(url, headers=headers, auth=auth, params=params)
    
    if response.status_code != 200:
        print(f"Failed to fetch boards: {response.status_code} - {response.text}")
        return None
    
    boards = response.json().get('values', [])
    for board in boards:
        if board['name'].lower() == board_name.lower():
            return board['id']
    
    print(f"Board '{board_name}' not found.")
    return None

def get_sprint_id(jira_url, username, api_token, board_id, sprint_name, max_results=1000):
    """
    Fetches the Sprint ID for a given sprint name within a board, handling pagination.
    
    Args:
        jira_url (str): Base URL of the JIRA instance.
        username (str): JIRA account email.
        api_token (str): API token.
        board_id (int): ID of the board.
        sprint_name (str): Name of the sprint to search for.
        max_results (int): Maximum number of sprints to fetch.
        
    Returns:
        int: Sprint ID if found, else None.
    """
    url = f"{jira_url}/rest/agile/1.0/board/{board_id}/sprint"
    auth = HTTPBasicAuth(username, api_token)
    headers = {"Accept": "application/json"}
    
    start_at = 0
    page_size = 50  # JIRA Agile API allows a maximum of 100 per request
    total = None
    
    while True:
        params = {
            "startAt": start_at,
            "maxResults": page_size,
            "state": 'active, closed',  # Fetch all sprints regardless of their state
        }
        
        response = requests.get(url, headers=headers, auth=auth, params=params)
        
        if response.status_code != 200:
            print(f"Failed to fetch sprints: {response.status_code} - {response.text}")
            return None
        
        data = response.json()
        sprints = data.get('values', [])
        
        for sprint in sprints:
            if sprint['name'].lower() == sprint_name.lower():
                return sprint['id']
        
        if total is None:
            total = data.get('total', 0)
        
        start_at += len(sprints)
        
        if start_at >= total or start_at >= max_results:
            break
        
        # Respect rate limits
        t.sleep(0.1)
    
    print(f"Sprint '{sprint_name}' not found in Board ID {board_id}.")
    return None

def get_sprint_ids_by_criteria(jira_url, username, api_token, board_id, sprint_state='closed', max_results=1000):
    """
    Fetches Sprint IDs based on specific criteria (e.g., sprint state).
    
    Args:
        jira_url (str): Base URL of the JIRA instance.
        username (str): JIRA account email.
        api_token (str): API token.
        board_id (int): ID of the board.
        sprint_state (str): State of the sprints to fetch ('active', 'future', 'closed', 'all').
        max_results (int): Maximum number of sprints to fetch.
        
    Returns:
        list: List of Sprint IDs matching the criteria.
    """
    url = f"{jira_url}/rest/agile/1.0/board/{board_id}/sprint"
    auth = HTTPBasicAuth(username, api_token)
    headers = {"Accept": "application/json"}
    
    sprint_ids = []
    start_at = 0
    page_size = 50  # Adjust as needed
    
    while start_at < max_results:
        params = {
            "startAt": start_at,
            "maxResults": page_size,
            "state": sprint_state  # e.g., 'closed'
        }
        
        response = requests.get(url, headers=headers, auth=auth, params=params)
        
        if response.status_code != 200:
            print(f"Failed to fetch sprints: {response.status_code} - {response.text}")
            break
        
        data = response.json()
        sprints = data.get('values', [])
        
        for sprint in sprints:
            sprint_ids.append(sprint['id'])
        
        if len(sprints) < page_size:
            break  # No more sprints to fetch
        
        start_at += len(sprints)
        time.sleep(0.1)  # Respect rate limits
    
    return sprint_ids


def get_issues_in_sprint(jira_url, username, api_token, sprint_id, max_results=1000):
    """
    Fetches all issues in a given sprint.
    
    Args:
        jira_url (str): Base URL of the JIRA instance.
        username (str): JIRA account email.
        api_token (str): API token.
        sprint_id (int): ID of the sprint.
        max_results (int): Maximum number of issues to fetch.
        
    Returns:
        list: List of issue dictionaries.
    """
    url = f"{jira_url}/rest/agile/1.0/sprint/{sprint_id}/issue"
    auth = HTTPBasicAuth(username, api_token)
    headers = {"Accept": "application/json"}
    
    issues = []
    start_at = 0
    page_size = 100  # Maximum allowed by JIRA Agile API
    
    while start_at < max_results:
        params = {
            "startAt": start_at,
            "maxResults": min(page_size, max_results - start_at),
            "fields": "key,summary,issuetype,status,{0}".format(STORY_POINTS_FIELD)
        }
        
        response = requests.get(url, headers=headers, auth=auth, params=params)
        
        if response.status_code != 200:
            print(f"Failed to fetch issues: {response.status_code} - {response.text}")
            break
        
        data = response.json()
        batch_issues = data.get('issues', [])
        if not batch_issues:
            break
        
        issues.extend(batch_issues)
        
        if len(batch_issues) < page_size:
            break  # No more issues to fetch
        
        start_at += len(batch_issues)
        time.sleep(0.1)  # Respect rate limits
    
    return issues

def fetch_issue_changelog(jira_url, username, api_token, issue_key):
    """
    Fetches the changelog for a given JIRA issue.
    
    Args:
        jira_url (str): Base URL of the JIRA instance.
        username (str): JIRA account email.
        api_token (str): API token.
        issue_key (str): Key of the JIRA issue (e.g., 'PROJ-123').
        
    Returns:
        dict: JSON data of the issue with changelog, or None if failed.
    """
    url = f"{jira_url}/rest/api/3/issue/{issue_key}?expand=changelog&fields=key,created,status,{STORY_POINTS_FIELD}"
    auth = HTTPBasicAuth(username, api_token)
    headers = {"Accept": "application/json"}
    
    response = requests.get(url, headers=headers, auth=auth)
    
    if response.status_code != 200:
        print(f"Failed to fetch issue {issue_key}: {response.status_code} - {response.text}")
        return None
    
    return response.json()

def process_changelog(issue_data, selected_statuses, working_days, work_start_hour, work_end_hour, holidays):
    """
    Processes the changelog of a JIRA issue to calculate durations in selected statuses during business hours.
    
    Args:
        issue_data (dict): JSON data of the JIRA issue with changelog.
        selected_statuses (list): List of statuses to include in the analysis.
        working_days (list): List of integers representing working days.
        work_start_hour (int): Start hour of the workday.
        work_end_hour (int): End hour of the workday.
        holidays (list): List of holiday dates as strings.
        
    Returns:
        tuple: (story_points, list of status changes with business hours)
    """
    fields = issue_data.get('fields', {})
    
    # Extract Story Points
    story_points = fields.get(STORY_POINTS_FIELD, 'N/A')
    
    # Initialize variables
    status_changes = []
    creation_time_str = fields.get('created')
    
    # Parse creation time
    try:
        creation_time = datetime.strptime(creation_time_str, '%Y-%m-%dT%H:%M:%S.%f%z')
    except ValueError:
        # Handle cases where microseconds are not present
        creation_time = datetime.strptime(creation_time_str, '%Y-%m-%dT%H:%M:%S%z')
    
    # Convert to desired timezone
    desired_tz = pytz.timezone(TIMEZONE)
    creation_time = creation_time.astimezone(desired_tz)
    
    # Initial status
    status_info = fields.get('status', {})
    current_status = status_info.get('name', 'Unknown')
    current_time = creation_time
    
    # Process changelog
    changelog = issue_data.get('changelog', {}).get('histories', [])
    sorted_changelog = sorted(changelog, key=lambda x: x['created'])
    
    for history in sorted_changelog:
        for item in history['items']:
            if item['field'] == 'status':
                to_status = item['toString']
                timestamp_str = history['created']
                
                # Parse timestamp
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%f%z')
                except ValueError:
                    # Handle cases where microseconds are not present
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S%z')
                
                # Convert to desired timezone
                timestamp = timestamp.astimezone(desired_tz)
                
                # Check if current_status is in selected_statuses
                if current_status in selected_statuses:
                    # Calculate business hours between current_time and timestamp
                    duration = calculate_business_hours(
                        current_time,
                        timestamp,
                        working_days,
                        work_start_hour,
                        work_end_hour,
                        holidays
                    )
                    
                    status_changes.append({
                        'Status': current_status,
                        'Entered': current_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
                        'Exited': timestamp.strftime('%Y-%m-%d %H:%M:%S %Z'),
                        'Duration (Hours)': round(duration, 2)
                    })
                
                # Update current status and time
                current_status = to_status
                current_time = timestamp
    
    # Handle the current (last) status
    if current_status in selected_statuses:
        now = datetime.now(pytz.timezone(desired_tz.zone))
        duration = calculate_business_hours(
            current_time,
            now,
            working_days,
            work_start_hour,
            work_end_hour,
            holidays
        )
        status_changes.append({
            'Status': current_status,
            'Entered': current_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'Exited': 'N/A (Current Status)',
            'Duration (Hours)': round(duration, 2)
        })
    
    return story_points, status_changes

# ---------------------------- Main Process ---------------------------- #

def main():
    """
    Main function to fetch all issues in multiple sprints and export their details with business hours calculations.
    """
    # Step 1: Get Board ID
    board_id = get_board_id(JIRA_URL, USERNAME, API_TOKEN, BOARD_NAME)
    if not board_id:
        print("Exiting due to missing Board ID.")
        return
    
    print(f"Board ID for '{BOARD_NAME}': {board_id}")
    
    # Step 2: Get Sprint IDs
    sprint_ids = []
    for sprint_name in SPRINT_NAMES:
        sprint_id = get_sprint_id(JIRA_URL, USERNAME, API_TOKEN, board_id, sprint_name, max_results=MAX_SPRINTS)
        if sprint_id:
            sprint_ids.append((sprint_id, sprint_name))
            print(f"Sprint ID for '{sprint_name}': {sprint_id}")
        else:
            print(f"Skipping '{sprint_name}' as it was not found.")
    
    if not sprint_ids:
        print("No valid sprints found. Exiting.")
        return
    
    # Step 3: Get Issues in All Sprints
    all_issues_data = []
    
    for sprint_id, sprint_name in sprint_ids:
        print(f"\nFetching issues for Sprint '{sprint_name}' (ID: {sprint_id})")
        issues = get_issues_in_sprint(JIRA_URL, USERNAME, API_TOKEN, sprint_id, max_results=1000)
        print(f"Total issues fetched for '{sprint_name}': {len(issues)}")
        
        for idx, issue in enumerate(issues, start=1):
            issue_key = issue['key']
            print(f"Processing Issue {idx}/{len(issues)}: {issue_key}")
            
            issue_data = fetch_issue_changelog(JIRA_URL, USERNAME, API_TOKEN, issue_key)
            if not issue_data:
                print(f"Skipping issue {issue_key} due to fetch error.")
                continue
            
            try:
                story_points, status_durations = process_changelog(
                    issue_data,
                    SELECTED_STATUSES,
                    WORKING_DAYS,
                    WORK_START_HOUR,
                    WORK_END_HOUR,
                    HOLIDAYS
                )
            except Exception as e:
                print(f"Error processing issue {issue_key}: {e}")
                continue
            
            for status_entry in status_durations:
                all_issues_data.append({
                    'Sprint Name': sprint_name,  # Add Sprint Name
                    'Issue Key': issue_key,
                    'Issue URL': f"{JIRA_URL}/browse/{issue_key}",
                    'Story Points': story_points,
                    'Status': status_entry['Status'],
                    'Entered': status_entry['Entered'],
                    'Exited': status_entry['Exited'],
                    'Duration (Hours)': status_entry['Duration (Hours)']
                })
            
            # To respect API rate limits
            t.sleep(0.1)
    
    # Step 4: Export to CSV
    try:
        with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Sprint Name', 'Issue Key', 'Issue URL', 'Story Points', 'Status', 'Entered', 'Exited', 'Duration (Hours)']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in all_issues_data:
                writer.writerow(row)
        
        print(f"\nData has been exported to '{OUTPUT_CSV}'.")
    except Exception as e:
        print(f"Failed to write CSV file: {e}")

# ---------------------------- Entry Point ---------------------------- #

if __name__ == "__main__":
    main()
