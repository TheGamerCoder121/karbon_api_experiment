# Karbon API Wrapper

This project is an API wrapper for the Karbon API, designed to parse and structure data for budget to actual reporting, compatible with Power BI.

## Features

- Parses data from the Karbon API
- Structures data for easy integration with Power BI
- Implements authentication using HTTP Bearer and API Key
- Includes a debug mode with mock data for testing

## Setup

1. Clone the repository:
   ```
   git clone <repository-url>
   cd api_project
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Create a `.env` file in the root directory with the following content:
   ```
   KARBON_BEARER_TOKEN=your_bearer_token_here
   KARBON_ACCESS_KEY=your_access_key_here
   ```

4. Run the application:
   ```
   uvicorn app:app --reload
   ```

## API Endpoints

- `/billing`: Retrieve billing information
- `/work-items`: Fetch work items
- `/timesheets`: Get timesheet data
- `/budget-to-actual`: Generate budget to actual report

## Docker Deployment

1. Build the Docker image:
   ```
   docker build -t karbon-api-wrapper .
   ```

2. Run the Docker container:
   ```
   docker run -d -p 8000:8000 --name karbon-api-container karbon-api-wrapper
   ```

## Deployment

The application is prepared for deployment on AWS EC2 using Docker. Specific deployment instructions will be provided once AWS credentials are available.

## Development

To run the application in debug mode with mock data, set the `DEBUG_MODE` environment variable to `True`.

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE.md file for details.
