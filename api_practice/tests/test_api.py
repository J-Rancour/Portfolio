import pytest

from .conftest import RO, RW, obs


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_crud_roundtrip(client):
    r = client.post("/api/v1/observations", json=obs(station="kjfk"), headers=RW)
    assert r.status_code == 201
    created = r.json()
    assert created["station"] == "KJFK"  # normalised to upper case
    assert r.headers["location"] == f"/api/v1/observations/{created['id']}"

    assert client.get(r.headers["location"]).json() == created

    r = client.patch(f"/api/v1/observations/{created['id']}", json={"temperature_c": 25.5}, headers=RW)
    assert r.status_code == 200
    assert r.json()["temperature_c"] == 25.5
    assert r.json()["wind_speed_kt"] == 12  # untouched

    assert client.delete(f"/api/v1/observations/{created['id']}", headers=RW).status_code == 204
    assert client.get(f"/api/v1/observations/{created['id']}").status_code == 404


@pytest.mark.parametrize(
    "body",
    [
        {"station": "NOPE1"},
        obs(wind_dir_deg=400),
        obs(station="KJ"),
        obs(observed_at="not a date"),
        obs(temperature_c=10, dewpoint_c=12),  # cross-field rule
    ],
)
def test_invalid_bodies_return_422(client, body):
    r = client.post("/api/v1/observations", json=body, headers=RW)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"
    assert r.json()["error"]["details"]


def test_patch_cannot_null_a_required_field(client):
    oid = client.post("/api/v1/observations", json=obs(), headers=RW).json()["id"]
    r = client.patch(f"/api/v1/observations/{oid}", json={"temperature_c": None}, headers=RW)
    assert r.status_code == 422


def test_patch_revalidates_cross_field_rule(client):
    oid = client.post("/api/v1/observations", json=obs(temperature_c=18, dewpoint_c=10), headers=RW).json()["id"]
    r = client.patch(f"/api/v1/observations/{oid}", json={"temperature_c": 5}, headers=RW)
    assert r.status_code == 422


def test_duplicate_is_409(client):
    assert client.post("/api/v1/observations", json=obs(), headers=RW).status_code == 201
    r = client.post("/api/v1/observations", json=obs(), headers=RW)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "conflict"


def test_timezones_are_normalised_to_utc(client):
    r = client.post("/api/v1/observations", json=obs(observed_at="2026-10-11T14:51:00-04:00"), headers=RW)
    assert r.json()["observed_at"] == "2026-10-11T18:51:00Z"


def test_pagination_and_filters(client):
    for hour in (12, 13, 14):
        client.post("/api/v1/observations", json=obs(observed_at=f"2026-10-11T{hour}:00:00Z"), headers=RW)
    client.post("/api/v1/observations", json=obs(station="KLAX"), headers=RW)

    page = client.get("/api/v1/observations?station=KJFK&limit=2", headers=RW).json()
    assert page["total"] == 3
    assert [o["observed_at"][11:13] for o in page["items"]] == ["14", "13"]  # newest first

    page2 = client.get("/api/v1/observations?station=KJFK&limit=2&offset=2", headers=RW).json()
    assert [o["observed_at"][11:13] for o in page2["items"]] == ["12"]

    since = client.get("/api/v1/observations?station=KJFK&since=2026-10-11T13:00:00Z", headers=RW).json()
    assert since["total"] == 2

    assert client.get("/api/v1/observations?limit=500", headers=RW).status_code == 422


@pytest.mark.parametrize(
    "headers, status",
    [({}, 401), ({"X-API-Key": "wrong"}, 401), (RO, 403), (RW, 201)],
)
def test_write_auth(client, headers, status):
    r = client.post("/api/v1/observations", json=obs(), headers=headers)
    assert r.status_code == status
    if status == 401:
        assert r.headers["www-authenticate"] == "ApiKey"


def test_reads_are_public(client):
    assert client.get("/api/v1/observations").status_code == 200


def test_request_id_is_echoed_and_in_errors(client):
    r = client.get("/api/v1/observations/missing", headers={"X-Request-ID": "abc-123"})
    assert r.status_code == 404
    assert r.headers["x-request-id"] == "abc-123"
    assert r.json()["request_id"] == "abc-123"
    assert "x-process-time-ms" in r.headers


def test_metrics_count_requests(client):
    client.get("/health")
    client.get("/api/v1/observations/missing")
    m = client.get("/metrics").json()
    assert m["requests_total"] == 2  # the /metrics call itself is counted after it responds
    assert m["by_status"] == {"200": 1, "404": 1}


def test_cors_exposes_rate_limit_headers(client):
    r = client.get("/api/v1/observations", headers={**RW, "Origin": "http://localhost:5500"})
    assert r.headers["access-control-allow-origin"] == "http://localhost:5500"
    assert "x-ratelimit-remaining" in r.headers["access-control-expose-headers"].lower()
