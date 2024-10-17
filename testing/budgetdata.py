import http.client
import json
from config import KARBON_BEARER_TOKEN, KARBON_ACCESS_KEY  # Using your config file for credentials

API_BASE_URL = "api.karbonhq.com"

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

    if response.status == 200:
        return json.loads(data)
    else:
        print(f"Failed to fetch data from {endpoint}: {response.status}, {response.reason}")
        return None

# Fetch timesheets to get actual hours
def fetch_timesheets():
    print("Fetching timesheets...")
    endpoint = "/v3/Timesheets"
    timesheets_data = make_http_request("GET", endpoint)
    if timesheets_data:
        print(f"Fetched {len(timesheets_data.get('value', []))} timesheets.")
        return timesheets_data.get("value", [])
    else:
        print("No timesheets found.")
        return []

# Fetch work items to get budgeted hours
def fetch_work_items():
    print("Fetching work items...")
    endpoint = "/v3/WorkItems"  # Assuming this is the correct endpoint for budgeted hours
    work_items_data = make_http_request("GET", endpoint)
    if work_items_data:
        print(f"Fetched {len(work_items_data.get('value', []))} work items.")
        return work_items_data.get("value", [])
    else:
        print("No work items found.")
        return []

# Helper function to fetch client name
def get_client_name(client_key):
    if not client_key:
        return "Unknown Client"
    print(f"Fetching client with key: {client_key}")
    endpoint = f"/v3/Clients/{client_key}"
    client_data = make_http_request("GET", endpoint)
    if client_data:
        return client_data.get("Name", "Unknown Client")
    return "Unknown Client"

# Helper function to fetch user (worker) name
def get_user_name(user_key):
    if not user_key:
        return "Unknown Worker"
    print(f"Fetching worker with key: {user_key}")
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

    # Match timesheet entries with work items and gather data by client, worker, and task
    for timesheet in timesheets:
        user_name = get_user_name(timesheet["UserKey"])

        for entry in timesheet.get("TimeEntries", []):
            client_name = get_client_name(entry["ClientKey"])
            task_type = entry.get("TaskTypeName", "Unknown Task")
            actual_hours = entry["Minutes"] / 60  # Convert minutes to hours

            # Find the corresponding work item (task) for budgeted hours
            budgeted_hours = None
            for work_item in work_items:
                if work_item.get("WorkItemKey") == entry.get("EntityKey"):
                    budgeted_hours = work_item.get("BudgetedMinutes", 0) / 60  # Convert minutes to hours
                    break

            # Structure the data for easy analysis
            result.append({
                "Client": client_name,
                "Worker": user_name,
                "Task": task_type,
                "Actual Hours": actual_hours,
                "Budgeted Hours": budgeted_hours
            })

    return result

# Main function to run the program and print results
def main():
    print("Starting the process...")
    data = process_data()
    
    if not data:
        print("No data to display.")
        return

    # Output the structured data
    for entry in data:
        print(f"Client: {entry['Client']}, Worker: {entry['Worker']}, Task: {entry['Task']}, "
              f"Actual Hours: {entry['Actual Hours']:.2f}, Budgeted Hours: {entry['Budgeted Hours']:.2f}")

if __name__ == "__main__":
    main()
