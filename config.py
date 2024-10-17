import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access environment variables
KARBON_BEARER_TOKEN = os.getenv("KARBON_BEARER_TOKEN")
KARBON_ACCESS_KEY = os.getenv("KARBON_ACCESS_KEY")

# Karbon API base URL
KARBON_API_BASE_URL = "https://api.karbonhq.com"

# Date range for filtering timesheets (configurable)
START_DATE = "2024-10-01"  # Start of the date range (inclusive)
END_DATE = "2024-10-31"    # End of the date range (inclusive)

# Logging control
VERBOSE_LOGGING = False  # Set to True for detailed logs
