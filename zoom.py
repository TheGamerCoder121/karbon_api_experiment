import http.client
import json
import csv
import time
from tqdm import tqdm
from urllib.parse import quote
from config import KARBON_BEARER_TOKEN, KARBON_ACCESS_KEY, VERBOSE_LOGGING, START_DATE, END_DATE

API_BASE_URL = "api.karbonhq.com"

def log(message):
    """Logs messages based on the verbose logging flag."""
    if VERBOSE_LOGGING:
        print(message)

# Helper function to make HTTP requests
def make_http_request(method, endpoint, retries=3, backoff_factor=1.0):
    for attempt in range(retries):
        conn = http.client.HTTPSConnection(API_BASE_URL)
        headers = {
            'AccessKey': KARBON_ACCESS_KEY,
            'Authorization': f'Bearer {KARBON_BEARER_TOKEN}',
            'Content-Type': 'application/json'
        }

        conn.request(method, endpoint, body=None, headers=headers)
        response = conn.getresponse()
        data = response.read().decode('utf-8')
        conn.close()

        # Log raw response for debugging
        log(f"Raw response from {endpoint}: {data}")

        if response.status == 200:
            return json.loads(data)
        elif response.status in [429, 500]:
            # Handle rate limiting or server errors
            wait_time = backoff_factor * (2 ** attempt)
            log(f"Rate limit exceeded or server error. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
        else:
            log(f"Failed to fetch data from {endpoint}: {response.status}, {response.reason}")
            return None

    log(f"Failed to fetch data from {endpoint} after {retries} retries.")
    return None

# Fetch timesheets
def fetch_timesheets():
    log(f"Fetching timesheets from {START_DATE} to {END_DATE}...")

    start_date = f"{START_DATE}T00:00:00Z"
    end_date = f"{END_DATE}T23:59:59Z"

    filter_query = quote(f"StartDate ge {start_date} and EndDate le {end_date}")

    endpoint = f"/v3/Timesheets?$filter={filter_query}&$expand=TimeEntries"

    timesheets_data = make_http_request("GET", endpoint)
    if timesheets_data:
        log(f"Fetched {len(timesheets_data.get('value', []))} timesheets for the specified date range.")
        return timesheets_data.get("value", [])
    else:
        log("No timesheets found for the specified date range.")
        return []

# Fetch contacts individually by ClientKeys
def fetch_contacts_by_keys(client_keys):
    log("Fetching contacts individually by ClientKeys...")
    clients = {}
    for client_key in tqdm(client_keys, desc="Fetching contacts"):
        client_name = fetch_contact_by_key(client_key)
        if client_name:
            clients[client_key] = client_name
        else:
            clients[client_key] = "Unknown Client"
    log(f"Total contacts fetched: {len(clients)}")
    return clients

# Fetch a single contact by ContactKey
def fetch_contact_by_key(contact_key):
    endpoint = f"/v3/Contacts/{contact_key}"
    contact_data = make_http_request("GET", endpoint)
    if contact_data:
        return contact_data.get("FullName")
    else:
        log(f"Could not fetch contact with key {contact_key}")
        return None

# Fetch users
def fetch_users():
    log("Fetching all users in one batch...")
    endpoint = "/v3/Users"
    users_data = make_http_request("GET", endpoint)
    if users_data:
        log(f"Fetched {len(users_data.get('value', []))} users.")
        return {user["Id"]: user["Name"] for user in users_data.get("value", [])}
    else:
        log("No users found.")
        return {}

# Process data
def process_data():
    timesheets = fetch_timesheets()
    users = fetch_users()

    if not timesheets:
        log("No timesheets found for the specified date range.")
        return []

    # Collect all unique ClientKeys
    client_keys = set()
    for timesheet in timesheets:
        for entry in timesheet.get("TimeEntries", []):
            client_key = entry.get("ClientKey")
            if client_key:
                client_keys.add(client_key)

    # Fetch contacts based on ClientKeys
    clients = fetch_contacts_by_keys(client_keys)

    result = []
    with tqdm(total=len(timesheets), desc="Processing timesheets") as pbar:
        for timesheet in timesheets:
            user_name = users.get(timesheet["UserKey"], "Unknown Worker")

            for entry in timesheet.get("TimeEntries", []):
                client_key = entry.get("ClientKey")
                client_name = clients.get(client_key, "Unknown Client")

                task_type = entry.get("TaskTypeName", "Unknown Task")
                actual_hours = entry["Minutes"] / 60 if entry["Minutes"] is not None else 0

                result.append({
                    "Client": client_name,
                    "Worker": user_name,
                    "Task": task_type,
                    "Actual Hours": actual_hours,
                    "Budgeted Hours": 0
                })

            pbar.update(1)

    return result

# Write to CSV
def write_to_csv(data):
    log("Writing data to CSV file...")
    with open('output_data.csv', 'w', newline='') as csvfile:
        fieldnames = ['Client', 'Worker', 'Task', 'Actual Hours', 'Budgeted Hours']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for entry in data:
            writer.writerow(entry)
    log("CSV file written successfully.")

# Write to JSON
def write_to_json(data):
    log("Writing data to JSON file...")
    with open('output_data.json', 'w') as jsonfile:
        json.dump(data, jsonfile, indent=4)
    log("JSON file written successfully.")

# Main function
def main():
    log("Starting the process...")
    data = process_data()

    if not data:
        log("No data to display.")
        return

    write_to_csv(data)
    write_to_json(data)

    log("Data has been written to 'output_data.csv' and 'output_data.json'.")

if __name__ == "__main__":
    main()
