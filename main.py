import http.client
import json

conn = http.client.HTTPSConnection("api.karbonhq.com")
payload = ""

# Sample function to fetch timesheets from the Karbon API
def fetch_timesheets(api_url, headers):
    conn.request("GET", f'{api_url}?filter=start_date=2024-08-08&end_date=2024-08-16', payload, headers)
    response = conn.getresponse()
    result = response.read()
    return json.loads(result.decode("utf-8"))  # Parse the JSON string into a dictionary

# Parse timesheet data into a structured format
def parse_timesheets(data):
    structured_data = []
    for timesheet in data['value']:  # Now 'data' is a dictionary, so 'value' can be accessed
        structured_data.append({
            'TimesheetKey': timesheet['TimesheetKey'],
            'UserKey': timesheet['UserKey'],
            'StartDate': timesheet['StartDate'],
            'EndDate': timesheet['EndDate'],
            'Status': timesheet['Status'],
            'WorkItemCount': len(timesheet['WorkItemKeys'])
        })
    return structured_data

# Main function to fetch, parse, and save timesheets
def main():
    api_url = "/v3/Timesheets"  # The URL path for the request
    headers = {
        "AccessKey": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJLYXJib25IUSIsInJlZyI6InVzMiIsInRhayI6IkM4MTBCNjI5LTE4Q0YtNEJFQS1BOTA0LTIyREUzN0M3MkM3RSIsImlhdCI6MTcyODkzMjA2MC4wfQ.OxYZrn5qmHrdh-LfB8tSiP1CYBOyAFuGonjhLcHBLEc",
        "Authorization": "Bearer 1cb17015-7d73-4798-880e-0d59266c178a",
        "Content-Type": "application/json"
    }

    timesheet_data = fetch_timesheets(api_url, headers)
    parsed_data = parse_timesheets(timesheet_data)
    
    # For now, we will print the parsed data. You can save this to a CSV or database.
    print(json.dumps(parsed_data, indent=4))

if __name__ == '__main__':
    main()
