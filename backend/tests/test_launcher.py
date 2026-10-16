import socket

from app.launcher import is_free, pick_port
from tests.conftest import make_settings


def _occupied_port() -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    sock.listen()
    return sock


def test_preferred_port_is_used_when_free() -> None:
    sock = _occupied_port()
    free = sock.getsockname()[1]
    sock.close()
    assert pick_port(free) == free


def test_busy_port_falls_back_to_a_free_one() -> None:
    with _occupied_port() as sock:
        busy = sock.getsockname()[1]
        chosen = pick_port(busy)
        assert chosen != busy
        assert is_free(chosen)


def test_launch_port_origins_are_allowed() -> None:
    origins = make_settings(app_port=43210).allowed_origins
    assert "http://127.0.0.1:43210" in origins and "http://localhost:43210" in origins
    assert "http://127.0.0.1:8710" in origins
    assert make_settings().allowed_origins == make_settings(app_port=None).allowed_origins
