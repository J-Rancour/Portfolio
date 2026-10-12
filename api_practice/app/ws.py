"""WebSocket fan-out: every connected client gets each new observation.

HTTP is request/response, the client has to ask. A WebSocket starts as an HTTP
request with `Upgrade: websocket`, then stays open so the server can push.
"""

import logging

from fastapi import WebSocket, WebSocketDisconnect

log = logging.getLogger("api")


class Hub:
    def __init__(self):
        self.clients: set[WebSocket] = set()

    async def serve(self, ws: WebSocket) -> None:
        await ws.accept()
        self.clients.add(ws)
        try:
            await ws.send_json({"event": "hello", "clients": len(self.clients)})
            while True:
                # We don't expect client messages, but reading is how we notice
                # a disconnect. Answer "ping" so clients can test the link.
                if await ws.receive_text() == "ping":
                    await ws.send_json({"event": "pong"})
        except WebSocketDisconnect:
            pass
        finally:
            self.clients.discard(ws)

    async def broadcast(self, message: dict) -> None:
        for ws in list(self.clients):
            try:
                await ws.send_json(message)
            except Exception:
                # A dead socket must not break the request that triggered the broadcast.
                log.warning("dropping websocket client after failed send")
                self.clients.discard(ws)
