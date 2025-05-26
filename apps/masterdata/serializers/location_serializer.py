from rest_framework import serializers
from ..models import Location, Zone, LocationType

class ZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zone
        fields = ['id', 'zone_code', 'zone_name']

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