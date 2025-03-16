# battery_dashboard/config.py

# Redash API configuration
import os
REDASH_URL = os.getenv("REDASH_URL", "http://192.168.80.30:8080")
REDASH_API_KEY = os.getenv("REDASH_API_KEY", "FJBeHB2jfkXiNIClff27R2rdoO6W4UuGflX8EfJ4")
CELL_QUERY_ID = os.getenv("CELL_QUERY_ID", "24")
CYCLE_QUERY_ID = os.getenv("CYCLE_QUERY_ID", "28")