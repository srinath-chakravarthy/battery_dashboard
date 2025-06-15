# import subprocess
# import sys
# from battery_dashboard import main
#
# if __name__ == "__main__":
#     subprocess.run([
#         "panel", "serve", "battery_dashboard/main.py",
#         "--port", "8561",
#         "--address", "192.168.80.30",
#         "--allow-websocket-origin=*",
#         "--show",
#         "--autoreload"
#     ], check=True)
#

# !/usr/bin/env python3
"""
Simple runner for the Battery Analytics Dashboard
No subprocess calls - just imports and runs the Panel app directly
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import configuration to validate environment
try:
    from battery_dashboard.config import PANEL_HOST, PANEL_PORT, DEBUG, REDASH_API_KEY

    print("✓ Configuration loaded successfully")
except Exception as e:
    print(f"❌ Configuration error: {e}")
    print("Make sure you have created a .env file with the required variables")
    sys.exit(1)

# Import and run the dashboard
try:
    from battery_dashboard.main import create_app
    import panel as pn

    print("✓ Dashboard modules imported successfully")

    # Create the app
    app = create_app()

    # Serve the app
    print(f"🚀 Starting Battery Analytics Dashboard...")
    print(f"📍 URL: http://{PANEL_HOST}:{PANEL_PORT}")
    print(f"🔧 Debug mode: {DEBUG}")
    print("📊 Loading initial data...")

    # Use Panel's built-in server instead of subprocess
    pn.serve(
        app,
        port=PANEL_PORT,
        host=PANEL_HOST,
        show=True,  # Automatically open browser
        allow_websocket_origin=[PANEL_HOST, "localhost", "127.0.0.1"],
        autoreload=DEBUG,  # Enable autoreload in debug mode
        dev=DEBUG
    )

except KeyboardInterrupt:
    print("\n👋 Dashboard stopped by user")
except Exception as e:
    print(f"❌ Error starting dashboard: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)