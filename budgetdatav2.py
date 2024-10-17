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

# Fetch work items to get budgeted hours (assuming work items are under /v3/Work)
def fetch_work_items():
    log("Fetching work items...")
    endpoint = "/v3/Work"
    work_items_data = make_http_request("GET", endpoint)
    if work_items_data:
        log(f"Fetched {len(work_items_data.get('value', []))} work items.")
        return work_items_data.get("value", [])
    else:
        log("No work items found.")
        return []

# Helper function to fetch client name
def get_client_name(client_key):
    if not client_key:
        return "Unknown Client"
    log(f"Fetching client with key: {client_key}")
    endpoint = f"/v3/Clients/{client_key}"
    client_data = make_http_request("GET", endpoint)
    if client_data:
        return client_data.get("Name", "Unknown Client")
    return "Unknown Client"

# Helper function to fetch user (worker) name
def get_user_name(user_key):
    if not user_key:
        return "Unknown Worker"
    log(f"Fetching worker with key: {user_key}")
    endpoint = f"/v3/Users/{user_key}"
    user_data = make_http_request("GET", endpoint)
    if user_data:
        return user_data.get("Name", "Unknown Worker")
    return "Unknown Worker"

# Process and structure the data
def process_data():
    timesheets = fetch_timesheets()
    work_items = fetch_work_items()

    result = []

    # Create progress bar for processing timesheets
    with tqdm(total=len(timesheets), desc="Processing timesheets") as pbar:
        # Match timesheet entries with work items and gather data by client, worker, and task
        for timesheet in timesheets:
            user_name = get_user_name(timesheet["UserKey"])

            for entry in timesheet.get("TimeEntries", []):
                client_name = get_client_name(entry["ClientKey"])
                task_type = entry.get("TaskTypeName", "Unknown Task")
                actual_hours = entry["Minutes"] / 60 if entry["Minutes"] is not None else 0  # Convert minutes to hours

                # Find the corresponding work item (task) for budgeted hours
                budgeted_hours = None
                for work_item in work_items:
                    if work_item.get("WorkKey") == entry.get("EntityKey"):  # Match task/work items by WorkKey
                        budgeted_hours = work_item.get("BudgetedMinutes", 0) / 60  # Convert minutes to hours
                        break

                # Ensure budgeted_hours is not None
                if budgeted_hours is None:
                    budgeted_hours = 0

                # Structure the data for easy analysis
                result.append({
                    "Client": client_name,
                    "Worker": user_name,
                    "Task": task_type,
                    "Actual Hours": actual_hours,
                    "Budgeted Hours": budgeted_hours
                })
            
            # Update progress bar
            pbar.update(1)

    return result

# Write data to CSV
def write_to_csv(data):
    log("Writing data to CSV file...")
    with open('output_data.csv', 'w', newline='') as csvfile:
        fieldnames = ['Client', 'Worker', 'Task', 'Actual Hours', 'Budgeted Hours']
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
