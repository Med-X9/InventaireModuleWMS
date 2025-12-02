from rest_framework import serializers
from ..models import Location, SousZone, Zone, Warehouse, LocationType, Family
from .sous_zone_serializer import SousZoneSerializer
from .zone_serializer import ZoneSerializer
from .warehouse_serializer import WarehouseSerializer

class FamilySerializer(serializers.ModelSerializer):
    class Meta:
        model = Family
        fields = ['id', 'reference', 'family_name', 'family_description', 'family_status']

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

class UnassignedLocationSerializer(serializers.ModelSerializer):
    sous_zone = SousZoneSerializer(read_only=True)
    sous_zone_name = serializers.CharField(source='sous_zone.sous_zone_name', read_only=True)
    zone = serializers.SerializerMethodField()
    zone_name = serializers.CharField(source='sous_zone.zone.zone_name', read_only=True)
    warehouse = serializers.SerializerMethodField()
    families = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = [
            'id',
            'reference', 
            'location_reference',
            'description',
            'sous_zone',
            'sous_zone_name',
            'zone',
            'zone_name',
            'warehouse',
            'families'
        ]

    def get_zone(self, obj):
        if obj.sous_zone and hasattr(obj.sous_zone, 'zone'):
            return ZoneSerializer(obj.sous_zone.zone).data
        return None

    def get_warehouse(self, obj):
        if obj.sous_zone and hasattr(obj.sous_zone, 'zone') and obj.sous_zone.zone and hasattr(obj.sous_zone.zone, 'warehouse'):
            return WarehouseSerializer(obj.sous_zone.zone.warehouse).data
        return None

    def get_families(self, obj):
        """
        Récupère les familles des produits stockés dans cet emplacement
        """
        families = []
        family_ids = set()
        
        # Utiliser les stocks préchargés
        for stock in obj.stock_set.all():
            if stock.product and stock.product.Product_Family:
                family_id = stock.product.Product_Family.id
                if family_id not in family_ids:
                    family_ids.add(family_id)
                    families.append(FamilySerializer(stock.product.Product_Family).data)
        
        return families 