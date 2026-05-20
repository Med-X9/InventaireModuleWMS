"""
Surveille le registry Redis : si la clé de présence a expiré (plus de heartbeat),
diffuse un événement offline vers le groupe dashboard.

À lancer en parallèle du serveur ASGI (Supervisor, systemd, second conteneur, etc.) :

    python manage.py run_presence_monitor --interval 15
"""

import time

from django.core.management.base import BaseCommand

from apps.realtime.services.broadcast import broadcast_presence_sync
from apps.realtime.services.presence_store import (
    key_exists_sync,
    registry_members_sync,
    remove_registry_member_sync,
    sync_redis_client,
)


class Command(BaseCommand):
    help = "Détecte les présences mobiles expirées (TTL) et notifie le dashboard WebSocket."

    def add_arguments(self, parser):
        parser.add_argument(
            "--interval",
            type=float,
            default=15.0,
            help="Intervalle en secondes entre deux vérifications (défaut: 15).",
        )

    def handle(self, *args, **options):
        interval = max(5.0, float(options["interval"]))
        self.stdout.write(
            self.style.SUCCESS(
                f"Presence monitor démarré (intervalle={interval}s). Ctrl+C pour arrêter."
            )
        )
        while True:
            client = sync_redis_client()
            try:
                for user_id, device_id in registry_members_sync(client):
                    if not key_exists_sync(client, user_id, device_id):
                        broadcast_presence_sync(
                            user_id=user_id,
                            device_id=device_id,
                            status="offline",
                            reason="ttl_expired",
                        )
                        remove_registry_member_sync(client, user_id, device_id)
                        self.stdout.write(
                            f"Présence expirée (TTL) — user_id={user_id} device_id={device_id}"
                        )
            finally:
                client.close()
            time.sleep(interval)
