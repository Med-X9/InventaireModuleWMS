"""Constantes partagées pour la présence WebSocket."""

# Groupe Channels : tous les dashboards web abonnés reçoivent les événements.
PRESENCE_DASHBOARD_GROUP = "presence_dashboard"

# Clé Redis SET : membres JSON [user_id, device_id] pour le monitor TTL.
PRESENCE_REGISTRY_REDIS_KEY = "presence:registry"

# Préfixe des clés de présence (valeur = connection_id du consumer).
PRESENCE_KEY_PREFIX = "presence:user:"
