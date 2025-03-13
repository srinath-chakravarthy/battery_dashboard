import subprocess
import sys

if __name__ == "__main__":
    subprocess.run([
        "panel", "serve", "app.py",
        "--port", "8060",
        "--show"
    ], check=True)
