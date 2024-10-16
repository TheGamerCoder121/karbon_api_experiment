import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access environment variables
KARBON_BEARER_TOKEN = os.getenv("KARBON_BEARER_TOKEN")
KARBON_ACCESS_KEY = os.getenv("KARBON_ACCESS_KEY")

# Karbon API base URL
KARBON_API_BASE_URL = "https://api.karbonhq.com"
