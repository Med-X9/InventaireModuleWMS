from rest_framework import serializers

from apps.masterdata.models import Warehouse


class WarehouseListSerializer(serializers.ModelSerializer):
    """Serializer pour exposer les données d'entrepôt dans le contexte inventory."""

    class Meta:
        model = Warehouse
        fields = (
            "id",
            "reference",
            "warehouse_name",
            "warehouse_type",
            "status",
            "address",
        )

