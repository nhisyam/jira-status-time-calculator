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
