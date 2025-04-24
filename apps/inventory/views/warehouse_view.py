from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..services.warehouse_service import WarehouseService
from ..serializers.warehouse_serializer import WarehouseSerializer

class WarehouseListView(APIView):
    """
    Vue pour récupérer tous les entrepôts
    """
    def get(self, request):
        warehouses = WarehouseService.get_all_warehouses()
        serializer = WarehouseSerializer(warehouses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK) 