from rest_framework import serializers
from ..models import Warehouse

class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = [
            'id',
            'reference',
            'warehouse_name',
            'warehouse_type',
            'description',
            'status',
            'address'
        ] 