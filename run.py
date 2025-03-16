import subprocess
import sys
from battery_dashboard import main

if __name__ == "__main__":
    subprocess.run([
        "panel", "serve", "main.py",
        "--port", "8060",
        "--show",
        "--autoreload"
    ], check=True)
