from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.realtime.constants import PRESENCE_DASHBOARD_GROUP


class DashboardPresenceConsumer(AsyncJsonWebsocketConsumer):
    """
    Dashboard web : reçoit les événements de présence (online / offline).

    Connexion : ws(s)://.../ws/presence/dashboard/?token=<jwt_utilisateur_web>
    L'utilisateur doit être authentifié et de type Web (ou staff).
    """

    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return

        user_type = getattr(user, "type", None)
        if user_type != "Web" and not getattr(user, "is_staff", False):
            await self.close(code=4403)
            return

        await self.channel_layer.group_add(PRESENCE_DASHBOARD_GROUP, self.channel_name)
        await self.accept()
        await self.send_json(
            {
                "event": "system",
                "status": "subscribed",
                "message": "Écoute des événements de présence mobile activée.",
            }
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            PRESENCE_DASHBOARD_GROUP, self.channel_name
        )

    async def presence_notify(self, event):
        """Handler group_send type 'presence.notify'."""
        await self.send_json(event["data"])
