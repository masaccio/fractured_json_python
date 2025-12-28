from pathlib import Path

import pytest
import pythonnet


def pytest_addoption(parser):
    parser.addoption("--test-file", action="store", default=None)
    parser.addoption("--test-verbose", action="store_true", default=False)


@pytest.fixture
def path_is_file_fails(monkeypatch):
    """Make Path.is_file return False."""
    monkeypatch.setattr(Path, "is_file", lambda self: False)


@pytest.fixture
def path_is_file_succeeds(monkeypatch):
    """Make Path.is_file return True."""
    monkeypatch.setattr(Path, "is_file", lambda self: True)


@pytest.fixture
def pythonnet_load_raises(monkeypatch):
    """Make pythonnet.load raise RuntimeError while keeping the DLL present."""
    monkeypatch.setattr(Path, "is_file", lambda self: True)

    def _raise(runtime) -> None:
        _ = runtime
        msg = "failed to init runtime"
        raise RuntimeError(msg)

    monkeypatch.setattr(pythonnet, "load", _raise)
