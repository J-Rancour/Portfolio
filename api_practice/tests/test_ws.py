from .conftest import RW, obs


def test_new_observations_are_pushed(client):
    with client.websocket_connect("/ws/observations") as ws:
        assert ws.receive_json()["event"] == "hello"
        client.post("/api/v1/observations", json=obs(station="KSEA"), headers=RW)
        msg = ws.receive_json()
        assert msg["event"] == "observation.created"
        assert msg["data"]["station"] == "KSEA"


def test_ping_pong(client):
    with client.websocket_connect("/ws/observations") as ws:
        ws.receive_json()
        ws.send_text("ping")
        assert ws.receive_json() == {"event": "pong"}


def test_disconnected_clients_are_removed(client):
    with client.websocket_connect("/ws/observations") as ws:
        ws.receive_json()
        assert len(client.app.state.hub.clients) == 1
    client.post("/api/v1/observations", json=obs(), headers=RW)  # must not fail
    assert len(client.app.state.hub.clients) == 0
