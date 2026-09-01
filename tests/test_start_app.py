import socket

import pytest

import start_app


def test_port_is_available_for_unused_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(("127.0.0.1", 0))
        port = server.getsockname()[1]

    assert start_app.port_is_available(port)


def test_port_is_available_detects_listener():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(("127.0.0.1", 0))
        server.listen()
        port = server.getsockname()[1]

        assert not start_app.port_is_available(port)


def test_main_reports_occupied_ports(monkeypatch):
    monkeypatch.setattr(start_app, "port_is_available", lambda port: port != start_app.BACKEND_PORT)

    with pytest.raises(SystemExit, match="8000"):
        start_app.main()