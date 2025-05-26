from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from ..models import Zone
from ..serializers.zone_serializer import ZoneSerializer
from ..services.zone_service import ZoneService

class ZoneListView(APIView):
    """
    Vue pour la gestion des zones.
    Permet de lister les zones avec filtres.
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.zone_service = ZoneService()
    
    def get(self, request):
        """
        Récupère la liste des zones avec les filtres appliqués.
        
        Query Parameters:
            warehouse_id: ID de l'entrepôt pour filtrer les zones
            search: Terme de recherche pour filtrer par nom de zone
        """
        warehouse_id = request.query_params.get('warehouse_id')
        search = request.query_params.get('search')
        
        if warehouse_id:
            try:
                warehouse_id = int(warehouse_id)
            except ValueError:
                return Response(
                    {"error": "warehouse_id doit être un nombre entier"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        zones = self.zone_service.get_zones(warehouse_id, search)
        serializer = ZoneSerializer(zones, many=True)
        return Response(serializer.data)

class ZoneDetailView(APIView):
    """
    Vue pour la gestion des détails d'une zone.
    Permet de récupérer les détails d'une zone spécifique.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        """
        Récupère les détails d'une zone spécifique.
        
        Args:
            pk: ID de la zone à récupérer
        """
        try:
            zone = Zone.objects.get(pk=pk)
            serializer = ZoneSerializer(zone)
            return Response(serializer.data)
        except Zone.DoesNotExist:
            return Response(
                {"error": "Zone non trouvée"},
                status=status.HTTP_404_NOT_FOUND
            ) 