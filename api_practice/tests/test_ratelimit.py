from app import ratelimit
from app.ratelimit import TokenBucket

from .conftest import RW


class FakeClock:
    """Controls time.monotonic() so the test doesn't need to sleep."""

    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def test_token_bucket_burst_then_refill(monkeypatch):
    clock = FakeClock()
    monkeypatch.setattr(ratelimit.time, "monotonic", clock)
    bucket = TokenBucket(capacity=3, rate=1.0)

    assert [bucket.take()[0] for _ in range(4)] == [True, True, True, False]
    allowed, wait = bucket.take()
    assert not allowed and wait == 1.0

    clock.now += 1.0  # one token refills
    assert bucket.take()[0] is True
    assert bucket.take()[0] is False

    clock.now += 100  # refill never exceeds capacity
    assert [bucket.take()[0] for _ in range(4)] == [True, True, True, False]


def test_anonymous_clients_get_429_with_retry_after(client, settings):
    statuses = [client.get("/api/v1/observations").status_code for _ in range(settings.rate_capacity_anon + 1)]
    assert statuses[:-1] == [200] * settings.rate_capacity_anon
    r = client.get("/api/v1/observations")
    assert r.status_code == 429
    assert int(r.headers["retry-after"]) >= 1
    assert r.json()["error"]["code"] == "rate_limited"
    # a valid key has its own, separate bucket
    assert client.get("/api/v1/observations", headers=RW).status_code == 200


def test_fake_keys_share_the_anonymous_bucket(client, settings):
    for i in range(settings.rate_capacity_anon):
        client.get("/api/v1/observations", headers={"X-API-Key": f"fake-{i}"})
    assert client.get("/api/v1/observations", headers={"X-API-Key": "yet-another"}).status_code == 429


def test_health_is_not_rate_limited(client, settings):
    assert all(client.get("/health").status_code == 200 for _ in range(settings.rate_capacity_anon * 2))
