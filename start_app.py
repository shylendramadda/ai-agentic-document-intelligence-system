import socket
import subprocess
import sys
import time


BACKEND_PORT = 8000
FRONTEND_PORT = 8501


def port_is_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return sock.connect_ex(("127.0.0.1", port)) != 0


def wait_for_port(port: int, timeout: float = 15) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not port_is_available(port):
            return True
        time.sleep(0.1)
    return False


def terminate_process(process: subprocess.Popen) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def main() -> None:
    ports = (BACKEND_PORT, FRONTEND_PORT)
    occupied_ports = [port for port in ports if not port_is_available(port)]
    if occupied_ports:
        joined_ports = ", ".join(str(port) for port in occupied_ports)
        raise SystemExit(f"Cannot start application: port(s) already in use: {joined_ports}")

    backend = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.backend.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(BACKEND_PORT),
        ]
    )
    frontend = None
    try:
        if not wait_for_port(BACKEND_PORT):
            raise RuntimeError("Backend did not become ready within 15 seconds")

        frontend = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "app/frontend/streamlit_app.py",
                "--server.port",
                str(FRONTEND_PORT),
                "--server.address",
                "127.0.0.1",
            ]
        )
        print(f"Backend: http://127.0.0.1:{BACKEND_PORT}")
        print(f"Frontend: http://127.0.0.1:{FRONTEND_PORT}")

        while True:
            if backend.poll() is not None:
                raise RuntimeError(f"Backend exited with code {backend.returncode}")
            if frontend.poll() is not None:
                raise RuntimeError(f"Frontend exited with code {frontend.returncode}")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Stopping application...")
    finally:
        if frontend is not None:
            terminate_process(frontend)
        terminate_process(backend)


if __name__ == "__main__":
    main()
