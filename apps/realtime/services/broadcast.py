"""Diffusion des changements de présence vers le groupe dashboard."""

from __future__ import annotations

import time
from typing import Any

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from apps.realtime.constants import PRESENCE_DASHBOARD_GROUP


def build_presence_payload(
    *,
    user_id: int,
    device_id: str,
    status: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "event": "presence",
        "user_id": user_id,
        "device_id": device_id,
        "status": status,
        "reason": reason,
        "ts": int(time.time()),
    }


def broadcast_presence_sync(
    *,
    user_id: int,
    device_id: str,
    status: str,
    reason: str,
) -> None:
    """Appel synchrone (management command, signaux) vers le channel layer."""
    layer = get_channel_layer()
    payload = build_presence_payload(
        user_id=user_id, device_id=device_id, status=status, reason=reason
    )
    async_to_sync(layer.group_send)(
        PRESENCE_DASHBOARD_GROUP,
        {"type": "presence.notify", "data": payload},
    )
