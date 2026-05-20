"""
Authentification WebSocket via JWT (query string `token=`).
Compatible avec rest_framework_simplejwt (même clé de signature que l'API REST).
"""

from __future__ import annotations

import logging
from urllib.parse import parse_qs
from typing import Callable, Awaitable

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

logger = logging.getLogger(__name__)


@database_sync_to_async
def _get_user(user_id: int):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    try:
        return User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return AnonymousUser()


def _token_from_scope(scope: dict) -> str | None:
    qs = parse_qs(scope.get("query_string", b"").decode("utf-8"))
    tokens = qs.get("token") or qs.get("access")
    if not tokens:
        return None
    return tokens[0].strip() or None


class JWTAuthMiddleware(BaseMiddleware):
    """
    Remplit scope['user'] à partir du JWT passé en query string.

    Exemple d'URL WebSocket :
    /ws/presence/mobile/?token=<access_jwt>&device_id=scanner-01
    """

    async def __call__(
        self,
        scope: dict,
        receive: Callable[[], Awaitable[dict]],
        send: Callable[[dict], Awaitable[None]],
    ):
        if scope["type"] != "websocket":
            return await super().__call__(scope, receive, send)

        token = _token_from_scope(scope)
        if not token:
            # Laisser AuthMiddlewareStack définir l'utilisateur (ex. session cookie pour le web).
            return await super().__call__(scope, receive, send)

        try:
            validated = AccessToken(token)
            uid = int(validated["user_id"])
        except (TokenError, KeyError, ValueError, TypeError) as e:
            logger.debug("JWT WebSocket invalide: %s", e)
            scope["user"] = AnonymousUser()
            return await super().__call__(scope, receive, send)

        scope["user"] = await _get_user(uid)
        return await super().__call__(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    """
    Session/cookies d'abord, puis JWT en query string écrase scope['user'] si token valide.
    """
    from channels.auth import AuthMiddlewareStack

    return AuthMiddlewareStack(JWTAuthMiddleware(inner))
