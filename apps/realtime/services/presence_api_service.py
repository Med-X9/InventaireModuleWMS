"""
Service lecture présence pour l'API REST (dashboard web).
"""

from __future__ import annotations

from django.contrib.auth import get_user_model

from apps.realtime.services.presence_store import list_online_presences_sync

User = get_user_model()


class PresenceApiService:
    """Expose la liste des terminaux mobiles connectés (Redis uniquement)."""

    def get_connected_devices(self) -> dict:
        presences = list_online_presences_sync()
        if not presences:
            return {"count": 0, "devices": []}

        user_ids = {p["user_id"] for p in presences}
        users_by_id = {
            u.id: u
            for u in User.objects.filter(id__in=user_ids, type="Mobile", is_active=True)
        }

        devices = []
        for p in presences:
            user = users_by_id.get(p["user_id"])
            devices.append(
                {
                    "user_id": p["user_id"],
                    "device_id": p["device_id"],
                    "status": p["status"],
                    "ttl_remaining_seconds": p["ttl_remaining_seconds"],
                    "last_seen_at": p["last_seen_at"],
                    "username": user.username if user else None,
                    "nom": getattr(user, "nom", None) if user else None,
                    "prenom": getattr(user, "prenom", None) if user else None,
                }
            )

        devices.sort(key=lambda d: (d.get("username") or "", d["device_id"]))
        return {"count": len(devices), "devices": devices}
