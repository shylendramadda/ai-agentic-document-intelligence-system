import os
import subprocess
import sys
import threading
import time


def run_backend():
    subprocess.run(
        [sys.executable, "-m", "uvicorn", "app.backend.main:app", "--host", "0.0.0.0", "--port", "8000"],
        check=False,
    )


def run_frontend():
    time.sleep(2)
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", "app/frontend/streamlit_app.py", "--server.port", "8501"],
        check=False,
    )


if __name__ == "__main__":
    backend_thread = threading.Thread(target=run_backend, daemon=True)
    frontend_thread = threading.Thread(target=run_frontend, daemon=True)
    backend_thread.start()
    frontend_thread.start()
    print("Starting backend and frontend...")
    print("Open http://localhost:8501 for the Streamlit app")
    print("Open http://localhost:8000/docs for the FastAPI docs")
    while True:
        time.sleep(1)
