import subprocess
import sys

if __name__ == "__main__":
    subprocess.run([
        "streamlit", "run", "app.py",
        "--server.port", "8060"
    ], check=True)