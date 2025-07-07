from rest_framework import serializers
from ..models import Location, SousZone, Zone, Warehouse, LocationType
from .sous_zone_serializer import SousZoneSerializer
from .zone_serializer import ZoneSerializer
from .warehouse_serializer import WarehouseSerializer

class LocationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationType
        fields = ['id', 'code', 'name']

class LocationSerializer(serializers.ModelSerializer):
    sous_zone_name = serializers.CharField(source='sous_zone.sous_zone_name', read_only=True)
    # zone_name = serializers.CharField(source='sous_zone.zone.zone_name', read_only=True)
    # warehouse_name = serializers.CharField(source='sous_zone.zone.warehouse.warehouse_name', read_only=True)

    class Meta:
        model = Location
        fields = [
            'id',
            'sous_zone_name',
            'location_reference',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    # zone = ZoneSerializer()
    # location_type = LocationTypeSerializer()
    
    # class Meta:
    #     model = Location
    #     fields = [
    #         'id',
    #         'location_reference',
    #        
    #     ] 

class UnassignedLocationSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    reference = serializers.CharField()
    location_reference = serializers.CharField()
    description = serializers.CharField(allow_null=True, allow_blank=True)
    
    # location_type = serializers.DictField(required=False, allow_null=True)
    sous_zone = SousZoneSerializer()
    zone = serializers.SerializerMethodField()
    warehouse = serializers.SerializerMethodField()

    def get_zone(self, obj):
        if obj.sous_zone and hasattr(obj.sous_zone, 'zone'):
            return ZoneSerializer(obj.sous_zone.zone).data
        return None

    def get_warehouse(self, obj):
        if obj.sous_zone and hasattr(obj.sous_zone, 'zone') and obj.sous_zone.zone and hasattr(obj.sous_zone.zone, 'warehouse'):
            return WarehouseSerializer(obj.sous_zone.zone.warehouse).data
        return None 