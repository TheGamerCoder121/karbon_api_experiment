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
    filter_query = quote(f"StartDate ge {start_date} and EndDate le {end_date}", safe='')
    
    # Construct the endpoint with URL encoding
    endpoint = f"/v3/Timesheets?$filter={filter_query}&$expand=TimeEntries"
    
    timesheets_data = make_http_request("GET", endpoint)
    if timesheets_data:
        log(f"Fetched {len(timesheets_data.get('value', []))} timesheets for the specified date range.")
        return timesheets_data.get("value", [])
    else:
        log("No timesheets found for the specified date range.")
        return []

# Fetch all contacts with ContactType 'Client' and pagination
def fetch_contacts():
    log("Fetching all contacts with ContactType 'Client' in batches of 100...")
    filter_value = "ContactType eq 'Client'"
    encoded_filter = quote(filter_value, safe='')
    endpoint = f"/v3/Contacts?$filter={encoded_filter}"
    contacts = {}
    
    next_link = endpoint
    while next_link:
        contacts_data = make_http_request("GET", next_link)
        if contacts_data:
            for contact in contacts_data.get("value", []):
                contacts[contact["ContactKey"]] = contact["FullName"]
            next_link = contacts_data.get("@odata.nextLink", None)
            # If next_link is relative, ensure it starts with '/'
            if next_link and not next_link.startswith('/'):
                next_link = '/' + next_link
            # Remove the API base URL if present in the next_link
            if next_link and next_link.startswith("https://"):
                next_link = next_link.split(API_BASE_URL)[-1]
        else:
            log("Failed to fetch contacts.")
            next_link = None  # Exit the loop

    log(f"Fetched {len(contacts)} contacts with ContactType 'Client'.")
    return contacts

# Fetch all users individually
def fetch_users(user_keys):
    log("Fetching users individually...")
    users = {}
    with tqdm(total=len(user_keys), desc="Fetching users") as pbar:
        for user_key in user_keys:
            endpoint = f"/v3/Users/{user_key}"
            user_data = make_http_request("GET", endpoint)
            if user_data:
                users[user_key] = user_data.get("Name", "Unknown User")
            else:
                users[user_key] = "Unknown User"
            pbar.update(1)
    return users

# Process and structure the data
def process_data():
    timesheets = fetch_timesheets()
    contacts = fetch_contacts()  # Fetch contacts with ContactType 'Client'

    # Extract unique UserKeys from timesheets
    user_keys = set()
    for timesheet in timesheets:
        user_keys.add(timesheet["UserKey"])
    
    users = fetch_users(user_keys)  # Fetch users individually

    result = []

    # Create progress bar for processing timesheets
    with tqdm(total=len(timesheets), desc="Processing timesheets") as pbar:
        # Match timesheet entries with work items and gather data by contact, worker, and task
        for timesheet in timesheets:
            user_name = users.get(timesheet["UserKey"], "Unknown Worker")

            for entry in timesheet.get("TimeEntries", []):
                # Use 'ClientKey' from the entry
                client_key = entry.get("ClientKey")
                if not client_key:
                    log(f"No 'ClientKey' found in entry: {entry}")
                    contact_name = "Unknown Contact"
                else:
                    contact_name = contacts.get(client_key, "Unknown Contact")
                    if contact_name == "Unknown Contact":
                        log(f"ClientKey {client_key} not found in contacts.")
                
                task_type = entry.get("TaskTypeName", "Unknown Task")
                actual_hours = entry.get("Minutes", 0) / 60  # Convert minutes to hours

                # Structure the data for easy analysis
                result.append({
                    "Contact": contact_name,
                    "Worker": user_name,
                    "Task": task_type,
                    "Actual Hours": actual_hours,
                    "Budgeted Hours": 0  # Budgeted hours omitted until the Work API is functional
                })
            
            # Update progress bar
            pbar.update(1)

    return result

# Write data to CSV
def write_to_csv(data):
    log("Writing data to CSV file...")
    with open('output_data.csv', 'w', newline='') as csvfile:
        fieldnames = ['Contact', 'Worker', 'Task', 'Actual Hours', 'Budgeted Hours']
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
