import http.client
import json
import csv
from config import KARBON_BEARER_TOKEN, KARBON_ACCESS_KEY  # Import access token and key

# Constants
API_BASE_URL = "api.karbonhq.com"

# Helper function to make HTTP requests using http.client
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
        print(f"Failed to fetch data: {response.status}, {response.reason}")
        return None

# Helper function to fetch user details
def get_user_name(user_key):
    endpoint = f"/v3/Users/{user_key}"
    user_data = make_http_request("GET", endpoint)
    if user_data:
        return user_data.get("Name", "Unknown User")
    return "Unknown User"

# Helper function to fetch client details
def get_client_name(client_key):
    endpoint = f"/v3/Clients/{client_key}"
    client_data = make_http_request("GET", endpoint)
    if client_data:
        return client_data.get("Name", "Unknown Client")
    return "Unknown Client"

# Helper function to fetch entity details (e.g., tasks or projects)
def get_entity_name(entity_key):
    endpoint = f"/v3/Entities/{entity_key}"
    entity_data = make_http_request("GET", endpoint)
    if entity_data:
        return entity_data.get("Name", "Unknown Entity")
    return "Unknown Entity"

# Fetch timesheets
def fetch_timesheets():
    endpoint = "/v3/Timesheets"
    timesheets_data = make_http_request("GET", endpoint)
    if timesheets_data:
        return timesheets_data.get("value", [])
    else:
        print("No timesheets found.")
        return []

# Function to format timesheet data
def format_timesheet(timesheet):
    user_name = get_user_name(timesheet["UserKey"])
    formatted_timesheet = {
        "Timesheet ID": timesheet.get("TimesheetKey"),
        "Start Date": timesheet.get("StartDate"),
        "End Date": timesheet.get("EndDate"),
        "User": user_name,
        "Status": timesheet.get("Status"),
        "Time Entries": []
    }

    # Process each time entry in the timesheet
    for entry in timesheet.get("TimeEntries", []):
        client_name = get_client_name(entry["ClientKey"])
        entity_name = get_entity_name(entry["EntityKey"])

        formatted_entry = {
            "Task Type": entry.get("TaskTypeName", "Unknown Task"),
            "Role": entry.get("RoleName", "Unknown Role"),
            "Minutes": entry.get("Minutes"),
            "Hourly Rate": entry.get("HourlyRate"),
            "Client": client_name,
            "Entity": entity_name,
            "Billed Status": entry.get("BilledStatus", "Unknown Status")
        }
        formatted_timesheet["Time Entries"].append(formatted_entry)

    return formatted_timesheet

# Main program to fetch and format all timesheets
def main():
    timesheets = fetch_timesheets()
    formatted_timesheets = []

    if not timesheets:
        print("No timesheets found.")
        return

    for timesheet in timesheets:
        formatted_data = format_timesheet(timesheet)
        formatted_timesheets.append(formatted_data)

    # Save the formatted data as a JSON file
    with open('formatted_timesheets.json', 'w') as json_file:
        json.dump(formatted_timesheets, json_file, indent=4)
        print("Timesheet data saved to formatted_timesheets.json.")

    # Optionally, write to a CSV file for more user-friendly output
    with open('formatted_timesheets.csv', 'w', newline='') as csv_file:
        fieldnames = ["Timesheet ID", "Start Date", "End Date", "User", "Status", "Time Entries"]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for timesheet in formatted_timesheets:
            writer.writerow({
                "Timesheet ID": timesheet["Timesheet ID"],
                "Start Date": timesheet["Start Date"],
                "End Date": timesheet["End Date"],
                "User": timesheet["User"],
                "Status": timesheet["Status"],
                "Time Entries": json.dumps(timesheet["Time Entries"])  # Storing entries as JSON strings
            })

    print("Timesheet data saved to formatted_timesheets.csv.")

if __name__ == "__main__":
    main()
