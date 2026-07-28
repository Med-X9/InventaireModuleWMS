from rest_framework import serializers
from ..models import Setting


class SettingSerializer(serializers.ModelSerializer):
    """Serializer pour les paramètres."""
    account = serializers.StringRelatedField()
    warehouse = serializers.StringRelatedField()

    class Meta:
        model = Setting
        fields = ['id', 'account', 'warehouse']


class SettingStatusDetailSerializer(serializers.Serializer):
    """Réponse lecture statut Setting pour un couple inventaire / magasin."""

    setting_id = serializers.IntegerField()
    reference = serializers.CharField()
    status = serializers.CharField()
    inventory_id = serializers.IntegerField()
    inventory_reference = serializers.CharField(allow_null=True)
    inventory_label = serializers.CharField(allow_null=True)
    inventory_type = serializers.CharField(allow_null=True)
    warehouse_id = serializers.IntegerField()
    warehouse_name = serializers.CharField(allow_null=True)
    warehouse_reference = serializers.CharField(allow_null=True)
    warehouse_date = serializers.DateField(allow_null=True)
    status_date_lancement = serializers.DateTimeField(allow_null=True)
    status_date_termine = serializers.DateTimeField(allow_null=True)
    status_date_analyse = serializers.DateTimeField(allow_null=True)
    status_date_cloture = serializers.DateTimeField(allow_null=True)


class MultiWarehouseLaunchSerializer(serializers.Serializer):
    """Body pour le lancement multi-magasins (sélection)."""

    warehouse_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
        help_text="Liste des IDs magasins / warehouses à lancer",
    )
