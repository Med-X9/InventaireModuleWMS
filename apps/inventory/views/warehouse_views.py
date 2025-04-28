from rest_framework.views import APIView
from rest_framework.response import Response
from apps.masterdata.models import Warehouse
from apps.inventory.serializers.warehouse_serializer import WarehouseSerializer

class WarehouseListView(APIView):
    """
    API View pour gérer les entrepôts
    """
    def get(self, request, *args, **kwargs):
        warehouses = Warehouse.objects.all()
        serializer = WarehouseSerializer(warehouses, many=True)
        return Response(serializer.data) 