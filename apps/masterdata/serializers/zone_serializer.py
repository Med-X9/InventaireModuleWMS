from rest_framework import serializers
from ..models import Zone

class ZoneSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle Zone.
    """
    warehouse_name = serializers.CharField(source='warehouse.warehouse_name', read_only=True)
    
    class Meta:
        model = Zone
        fields = [
            'id',
            'warehouse',
            'warehouse_name',
            'zone_name',
            'zone_status',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at'] 