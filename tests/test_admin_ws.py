import asyncio
import json
from starlette.websockets import WebSocketState

from backend.routers import admin as admin_router

class DummyWS:
    def __init__(self):
        self.sent = []
        self.client_state = WebSocketState.CONNECTED

    async def send_text(self, msg):
        self.sent.append(msg)


def test_broadcast_admin_event():
    ws = DummyWS()
    admin_router.connected_admins = [ws]
    asyncio.run(admin_router.broadcast_admin_event({"msg": "hi"}))
    assert ws.sent == [json.dumps({"msg": "hi"})]
