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
    # zone = ZoneSerializer()
    # location_type = LocationTypeSerializer()
    
    class Meta:
        model = Location
        fields = [
            'id',
            'location_reference',
           
        ] 