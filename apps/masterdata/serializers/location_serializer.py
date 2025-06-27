from rest_framework import serializers
from ..models import Location, SousZone, Zone, Warehouse, LocationType

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

class UnassignedLocationSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    reference = serializers.CharField()
    location_reference = serializers.CharField()
    description = serializers.CharField(allow_null=True, allow_blank=True)
    
    # location_type = serializers.DictField(required=False, allow_null=True)
    sous_zone = serializers.DictField()
    zone = serializers.DictField()
    warehouse = serializers.DictField() 