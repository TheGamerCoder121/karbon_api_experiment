import http.client
import json
import csv
from tqdm import tqdm
from urllib.parse import quote
from config import KARBON_BEARER_TOKEN, KARBON_ACCESS_KEY, VERBOSE_LOGGING, START_DATE, END_DATE

API_BASE_URL = "api.karbonhq.com"

def log(message):
    """Logs messages based on the verbose logging flag."""
    if VERBOSE_LOGGING:
        print(message)

# Helper function to make HTTP requests
def make_http_request(method, endpoint):
    conn = http.client.HTTPSConnection(API_BASE_URL)
    headers = {
        'AccessKey': KARBON_ACCESS_KEY,
        'Authorization': f'Bearer {KARBON_BEARER_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    conn.request(method, endpoint, headers=headers)
    response = conn.getresponse()
    data = response.read().decode('utf-8')
    conn.close()

    # Log raw response for debugging only if verbose logging is enabled
    log(f"Raw response from {endpoint}: {data}")

    if response.status == 200:
        return json.loads(data)
    else:
        log(f"Failed to fetch data from {endpoint}: {response.status}, {response.reason}")
        return None

# Fetch timesheets to get actual hours, filtered by date range
def fetch_timesheets():
    log(f"Fetching timesheets from {START_DATE} to {END_DATE}...")

    # Format dates to ISO 8601 format with time and timezone (UTC)
    start_date = f"{START_DATE}T00:00:00Z"
    end_date = f"{END_DATE}T23:59:59Z"

    # URL-encode the filter part to handle spaces and special characters
    filter_query = quote(f"StartDate ge {start_date} and EndDate le {end_date}")
    
    # Construct the endpoint with URL encoding
    endpoint = f"/v3/Timesheets?$filter={filter_query}&$expand=TimeEntries"
    
    timesheets_data = make_http_request("GET", endpoint)
    if timesheets_data:
        log(f"Fetched {len(timesheets_data.get('value', []))} timesheets for the specified date range.")
        return timesheets_data.get("value", [])
    else:
        log("No timesheets found for the specified date range.")
        return []

# Fetch all clients in one batch
def fetch_clients():
    log("Fetching all clients in one batch...")
    endpoint = "/v3/Clients"
    clients_data = make_http_request("GET", endpoint)
    if clients_data:
        log(f"Fetched {len(clients_data.get('value', []))} clients.")
        return {client["ClientKey"]: client["Name"] for client in clients_data.get("value", [])}
    else:
        log("No clients found.")
        return {}

# Fetch all users in one batch
def fetch_users():
    log("Fetching all users in one batch...")
    endpoint = "/v3/Users"
    users_data = make_http_request("GET", endpoint)
    if users_data:
        log(f"Fetched {len(users_data.get('value', []))} users.")
        return {user["UserKey"]: user["Name"] for user in users_data.get("value", [])}
    else:
        log("No users found.")
        return {}

# Fetch estimate summaries for a work item using WorkItemKey
def fetch_estimate_summary(work_item_key):
    log(f"Fetching estimate summary for WorkItemKey: {work_item_key}")
    endpoint = f"/v3/EstimateSummaries/{work_item_key}"
    estimate_data = make_http_request("GET", endpoint)
    if estimate_data:
        log(f"Fetched estimate summary for WorkItemKey: {work_item_key}")
        return estimate_data.get("value", [])
    else:
        log(f"No estimate summary found for WorkItemKey: {work_item_key}")
        return []

# Process and structure the data
def process_data():
    timesheets = fetch_timesheets()
    clients = fetch_clients()  # Fetch clients once
    users = fetch_users()      # Fetch users once

    result = []

    # Create progress bar for processing timesheets
    with tqdm(total=len(timesheets), desc="Processing timesheets") as pbar:
        # Match timesheet entries with work items and gather data by client, worker, and task
        for timesheet in timesheets:
            user_name = users.get(timesheet["UserKey"], "Unknown Worker")

            for entry in timesheet.get("TimeEntries", []):
                client_name = clients.get(entry["ClientKey"], "Unknown Client")
                task_type = entry.get("TaskTypeName", "Unknown Task")
                actual_hours = entry["Minutes"] / 60 if entry["Minutes"] is not None else 0  # Convert minutes to hours

                # Fetch estimate summaries for the work item
                estimate_summary = fetch_estimate_summary(entry["EntityKey"])
                budgeted_hours = 0
                estimate_actual_hours = 0

                # If estimate summary is found, extract budgeted and actual hours
                if estimate_summary:
                    for estimate in estimate_summary:
                        estimate_minutes = estimate.get("EstimateMinutes")
                        actual_minutes = estimate.get("ActualMinutes")

                        # Ensure we don't divide None values; default to 0 if None
                        budgeted_hours += (estimate_minutes or 0) / 60  # Convert minutes to hours
                        estimate_actual_hours += (actual_minutes or 0) / 60  # Convert minutes to hours

                # Structure the data for easy analysis
                result.append({
                    "Client": client_name,
                    "Worker": user_name,
                    "Task": task_type,
                    "Actual Hours": actual_hours,
                    "Budgeted Hours": budgeted_hours,
                    "Estimate Actual Hours": estimate_actual_hours
                })
            
            # Update progress bar
            pbar.update(1)

    return result

# Write data to CSV
def write_to_csv(data):
    log("Writing data to CSV file...")
    with open('output_data.csv', 'w', newline='') as csvfile:
        fieldnames = ['Client', 'Worker', 'Task', 'Actual Hours', 'Budgeted Hours', 'Estimate Actual Hours']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for entry in data:
            writer.writerow(entry)
    log("CSV file written successfully.")

# Write data to JSON
def write_to_json(data):
    log("Writing data to JSON file...")
    with open('output_data.json', 'w') as jsonfile:
        json.dump(data, jsonfile, indent=4)
    log("JSON file written successfully.")

# Main function to run the program
def main():
    log("Starting the process...")
    data = process_data()
    
    if not data:
        log("No data to display.")
        return

    # Write the data to CSV and JSON
    write_to_csv(data)
    write_to_json(data)

    log("Data has been written to 'output_data.csv' and 'output_data.json'.")

if __name__ == "__main__":
    main()
