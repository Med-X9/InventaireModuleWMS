from rest_framework import serializers
from ..models import Setting


class SettingSerializer(serializers.ModelSerializer):
    """Serializer pour les paramètres."""
    account = serializers.StringRelatedField()
    warehouse = serializers.StringRelatedField()

    class Meta:
        model = Setting
        fields = ['id', 'account', 'warehouse']


class MultiWarehouseLaunchSerializer(serializers.Serializer):
    """Body pour le lancement multi-magasins (sélection)."""

    warehouse_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
        help_text="Liste des IDs magasins / warehouses à lancer",
    )
