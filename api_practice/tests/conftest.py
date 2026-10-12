import os

# Set before importing app.main, whose module-level `app` would otherwise create data/observations.json.
os.environ.setdefault("DB_PATH", ":memory:")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402

RW = {"X-API-Key": "dev-key-123"}
RO = {"X-API-Key": "readonly-key-789"}


def obs(**overrides):
    body = {
        "station": "KJFK",
        "observed_at": "2026-10-11T18:51:00Z",
        "temperature_c": 18,
        "dewpoint_c": 10,
        "wind_dir_deg": 270,
        "wind_speed_kt": 12,
        "visibility_sm": 10,
    }
    return {**body, **overrides}


@pytest.fixture
def settings():
    return Settings(db_path=":memory:")


@pytest.fixture
def client(settings):
    # A brand-new app + empty in-memory DB per test: no state leaks between tests.
    with TestClient(create_app(settings)) as c:
        yield c
