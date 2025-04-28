"""
Vues pour l'application inventory.
"""
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from apps.inventory.models import Inventory
from ..serializers.inventory_serializer import InventorySerializer
from ..services.inventory_service import InventoryService

class InventoryCreateView(APIView):
    """
    View pour gérer la création des inventaires
    """
    def get_serializer(self, *args, **kwargs):
        """Retourne le serializer approprié."""
        return InventorySerializer(*args, **kwargs)

    def get_queryset(self):
        return Inventory.objects.all().order_by('-created_at')

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Crée un nouvel inventaire."""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 