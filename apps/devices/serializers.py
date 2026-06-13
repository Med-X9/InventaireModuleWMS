from rest_framework import serializers

from apps.devices.models import Device
from apps.inventory.models import Inventory
from apps.masterdata.models import Warehouse


class HeartbeatSerializer(serializers.Serializer):
    device_id = serializers.CharField(max_length=128)
    battery_level = serializers.IntegerField(
        required=False, allow_null=True, min_value=0, max_value=100
    )
    is_charging = serializers.BooleanField(required=False, default=False)
    app_version = serializers.CharField(
        required=False, allow_blank=True, max_length=20, default=""
    )
    warehouse_id = serializers.IntegerField(required=False, allow_null=True)
    inventory_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_device_id(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("device_id est obligatoire.")
        return value

    def validate_warehouse_id(self, value):
        if value is None:
            return None
        if not Warehouse.objects.filter(pk=value, is_deleted=False).exists():
            raise serializers.ValidationError("Entrepôt introuvable.")
        return value

    def validate_inventory_id(self, value):
        if value is None:
            return None
        if not Inventory.objects.filter(pk=value, is_deleted=False).exists():
            raise serializers.ValidationError("Inventaire introuvable.")
        return value
