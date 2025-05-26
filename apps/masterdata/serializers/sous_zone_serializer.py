from rest_framework import serializers
from ..models import SousZone

class SousZoneSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle SousZone.
    """
    zone_name = serializers.CharField(source='zone.zone_name', read_only=True)
    # warehouse_name = serializers.CharField(source='zone.warehouse.warehouse_name', read_only=True)
    
    class Meta:
        model = SousZone
        fields = ['id', 'sous_zone_name', 'zone_name']
        read_only_fields = ['created_at', 'updated_at'] 