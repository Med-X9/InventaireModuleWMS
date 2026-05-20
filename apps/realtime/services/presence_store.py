"""
Stockage volatile de la présence dans Redis (TTL + registry pour le monitor).
Aucune écriture en base SQL.
"""

from __future__ import annotations

import json
import time
from typing import Optional, Tuple

import redis.asyncio as aioredis
import redis as sync_redis
from django.conf import settings

from apps.realtime.constants import PRESENCE_KEY_PREFIX, PRESENCE_REGISTRY_REDIS_KEY


def _presence_key(user_id: int | str, device_id: str) -> str:
    safe_device = device_id.replace(":", "_")[:200]
    return f"{PRESENCE_KEY_PREFIX}{user_id}:device:{safe_device}"


def _registry_member(user_id: int | str, device_id: str) -> str:
    return json.dumps([int(user_id), device_id], separators=(",", ":"))


class PresenceStore:
    """Accès async Redis depuis les consumers Channels."""

    def __init__(self, client: aioredis.Redis):
        self._r = client

    @classmethod
    async def connect(cls) -> "PresenceStore":
        url = getattr(settings, "PRESENCE_REDIS_URL", "redis://127.0.0.1:6379/1")
        client = aioredis.from_url(url, decode_responses=True)
        return cls(client)

    async def aclose(self) -> None:
        await self._r.aclose()

    async def set_online(
        self, user_id: int | str, device_id: str, connection_id: str
    ) -> None:
        key = _presence_key(user_id, device_id)
        ttl = int(getattr(settings, "PRESENCE_TTL_SECONDS", 45))
        pipe = self._r.pipeline()
        pipe.set(key, connection_id, ex=ttl)
        pipe.sadd(PRESENCE_REGISTRY_REDIS_KEY, _registry_member(user_id, device_id))
        await pipe.execute()

    async def refresh_ttl(
        self, user_id: int | str, device_id: str, connection_id: str
    ) -> bool:
        """Renouvelle le TTL seulement si cette connexion est toujours propriétaire."""
        key = _presence_key(user_id, device_id)
        ttl = int(getattr(settings, "PRESENCE_TTL_SECONDS", 45))
        current = await self._r.get(key)
        if current != connection_id:
            return False
        await self._r.expire(key, ttl)
        return True

    async def clear_if_owner(
        self, user_id: int | str, device_id: str, connection_id: str
    ) -> bool:
        """
        Supprime la clé et retire le registry si le connection_id correspond.
        Retourne True si la présence a été supprimée (déconnexion effective).
        """
        key = _presence_key(user_id, device_id)
        current = await self._r.get(key)
        if current != connection_id:
            return False
        pipe = self._r.pipeline()
        pipe.delete(key)
        pipe.srem(PRESENCE_REGISTRY_REDIS_KEY, _registry_member(user_id, device_id))
        await pipe.execute()
        return True


def sync_redis_client() -> sync_redis.Redis:
    url = getattr(settings, "PRESENCE_REDIS_URL", "redis://127.0.0.1:6379/1")
    return sync_redis.from_url(url, decode_responses=True)


def registry_members_sync(client: sync_redis.Redis) -> list[Tuple[int, str]]:
    """Liste (user_id, device_id) depuis le SET registry."""
    raw = client.smembers(PRESENCE_REGISTRY_REDIS_KEY)
    out: list[Tuple[int, str]] = []
    for m in raw:
        try:
            pair = json.loads(m)
            out.append((int(pair[0]), str(pair[1])))
        except (json.JSONDecodeError, TypeError, IndexError, ValueError):
            continue
    return out


def key_exists_sync(client: sync_redis.Redis, user_id: int, device_id: str) -> bool:
    return bool(client.exists(_presence_key(user_id, device_id)))


def remove_registry_member_sync(
    client: sync_redis.Redis, user_id: int, device_id: str
) -> None:
    client.srem(PRESENCE_REGISTRY_REDIS_KEY, _registry_member(user_id, device_id))


def now_ts() -> int:
    return int(time.time())


def list_online_presences_sync() -> list[dict]:
    """
    Liste les appareils actuellement en ligne (clé Redis présente).
    Source : registry + vérification EXISTS (pas de SQL).
    """
    client = sync_redis_client()
    try:
        members = registry_members_sync(client)
        ttl_default = int(getattr(settings, "PRESENCE_TTL_SECONDS", 45))
        now = now_ts()
        results: list[dict] = []

        for user_id, device_id in members:
            key = _presence_key(user_id, device_id)
            if not client.exists(key):
                continue
            ttl_remaining = client.ttl(key)
            if ttl_remaining < 0:
                ttl_remaining = ttl_default
            results.append(
                {
                    "user_id": user_id,
                    "device_id": device_id,
                    "status": "online",
                    "ttl_remaining_seconds": int(ttl_remaining),
                    "last_seen_at": now - max(0, ttl_default - int(ttl_remaining)),
                }
            )
        return results
    finally:
        client.close()
