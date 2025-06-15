# battery_dashboard/config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

REDASH_URL=os.getenv("REDASH_URL", "http://localhost:5000")
REDASH_API_KEY=os.getenv("REDASH_API_KEY")
CELL_QUERY_ID=os.getenv("CELL_QUERY_ID", 24)
CYCLE_QUERY_ID=os.getenv("CYCLE_QUERY_ID", 28)
ML_CYCLE_QUERY_ID=os.getenv("ML_CYCLE_QUERY_ID", 43)

# Application Configuration
LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO")
LOG_FILE=os.getenv("LOG_FILE", "battery_dashboard.log")
DEBUG=os.getenv("DEBUG", False)
CACHE_TTL=os.getenv("CACHE_TTL", 300)
MAX_CACHE_SIZE=os.getenv("MAX_CACHE_SIZE", 100)

# Panel Server Configuration
PANEL_PORT=int(os.getenv("PANEL_PORT", 8061))
PANEL_HOST=os.getenv("PANEL_HOST", "localhost")
PANEL_ALLOW_WEBSOCKET_ORIGIN=os.getenv("PANEL_ALLOW_WEBSOCKET_ORIGIN", "*")

# Validate critical configuration
if not REDASH_API_KEY:
    raise ValueError("REDASH_API_KEY environment variable is required")

print(f"Configuration loaded for {ENVIRONMENT} environment")
print(f"Redash URL: {REDASH_URL}")
print(f"Panel will run on: {PANEL_HOST}:{PANEL_PORT}")