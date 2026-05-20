import uuid
from urllib.parse import parse_qs

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

from apps.realtime.constants import PRESENCE_DASHBOARD_GROUP
from apps.realtime.services.broadcast import build_presence_payload
from apps.realtime.services.presence_store import PresenceStore


class MobilePresenceConsumer(AsyncJsonWebsocketConsumer):
    """
    Application mobile : maintient une présence volatile dans Redis (TTL).

    URL : /ws/presence/mobile/?token=<jwt>&device_id=<id_stable_terminal>

    Messages entrants JSON :
    - {"type": "heartbeat"} — renouvelle le TTL si la connexion est propriétaire.
    """

    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated or isinstance(user, AnonymousUser):
            await self.close(code=4401)
            return

        self.user_id = user.id

        if getattr(user, "type", None) != "Mobile":
            await self.close(code=4403)
            return

        qs = parse_qs(self.scope.get("query_string", b"").decode("utf-8"))
        device_parts = qs.get("device_id") or qs.get("device")
        self.device_id = (device_parts[0] if device_parts else "").strip() or "default"
        self.connection_id = str(uuid.uuid4())

        self._store = await PresenceStore.connect()
        await self._store.set_online(self.user_id, self.device_id, self.connection_id)

        await self.accept()

        await self.channel_layer.group_send(
            PRESENCE_DASHBOARD_GROUP,
            {
                "type": "presence.notify",
                "data": build_presence_payload(
                    user_id=self.user_id,
                    device_id=self.device_id,
                    status="online",
                    reason="connect",
                ),
            },
        )

    async def disconnect(self, close_code):
        cleared = False
        if (
            hasattr(self, "_store")
            and self._store
            and hasattr(self, "connection_id")
            and hasattr(self, "device_id")
        ):
            cleared = await self._store.clear_if_owner(
                self.user_id, self.device_id, self.connection_id
            )
            await self._store.aclose()

        if cleared and hasattr(self, "user_id") and hasattr(self, "device_id"):
            await self.channel_layer.group_send(
                PRESENCE_DASHBOARD_GROUP,
                {
                    "type": "presence.notify",
                    "data": build_presence_payload(
                        user_id=self.user_id,
                        device_id=self.device_id,
                        status="offline",
                        reason=f"disconnect:{close_code}",
                    ),
                },
            )

    async def receive_json(self, content, **kwargs):
        if not getattr(self, "_store", None):
            return
        if content.get("type") != "heartbeat":
            await self.send_json(
                {"event": "error", "message": "Type inconnu (attendu: heartbeat)."}
            )
            return

        ok = await self._store.refresh_ttl(
            self.user_id, self.device_id, self.connection_id
        )
        if ok:
            await self.send_json({"event": "heartbeat_ack", "ok": True})
        else:
            await self.send_json(
                {
                    "event": "heartbeat_ack",
                    "ok": False,
                    "message": "Session remplacée par une autre connexion.",
                }
            )
