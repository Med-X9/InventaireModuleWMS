from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from ..models import SousZone, Zone
from ..serializers.sous_zone_serializer import SousZoneSerializer
from ..services.sous_zone_service import SousZoneService

class SousZoneListView(APIView):
    """
    Vue pour la gestion des sous-zones.
    Permet de lister les sous-zones avec filtres.
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sous_zone_service = SousZoneService()
    
    def get(self, request):
        """
        Récupère la liste des sous-zones avec les filtres appliqués.
        
        Query Parameters:
            zone_id: ID de la zone pour filtrer les sous-zones
            search: Terme de recherche pour filtrer par nom de sous-zone
        """
        zone_id = request.query_params.get('zone_id')
        search = request.query_params.get('search')
        
        if zone_id:
            try:
                zone_id = int(zone_id)
            except ValueError:
                return Response(
                    {"error": "zone_id doit être un nombre entier"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        sous_zones = self.sous_zone_service.get_sous_zones(zone_id, search)
        serializer = SousZoneSerializer(sous_zones, many=True)
        return Response(serializer.data)

class SousZoneDetailView(APIView):
    """
    Vue pour la gestion des détails d'une sous-zone.
    Permet de récupérer les détails d'une sous-zone spécifique.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        """
        Récupère les détails d'une sous-zone spécifique.
        
        Args:
            pk: ID de la sous-zone à récupérer
        """
        try:
            sous_zone = SousZone.objects.get(pk=pk)
            serializer = SousZoneSerializer(sous_zone)
            return Response(serializer.data)
        except SousZone.DoesNotExist:
            return Response(
                {"error": "Sous-zone non trouvée"},
                status=status.HTTP_404_NOT_FOUND
            )

class ZoneSousZonesView(APIView):
    """
    Vue pour récupérer toutes les sous-zones d'une zone spécifique.
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sous_zone_service = SousZoneService()
    
    def get(self, request, zone_id):
        """
        Récupère toutes les sous-zones d'une zone spécifique.
        
        Args:
            zone_id: ID de la zone dont on veut récupérer les sous-zones
        """
        try:
            # Vérifier si la zone existe
            Zone.objects.get(pk=zone_id)
            
            # Récupérer les sous-zones de cette zone
            sous_zones = self.sous_zone_service.get_sous_zones(zone_id=zone_id)
            serializer = SousZoneSerializer(sous_zones, many=True)
            
            return Response(serializer.data)
            
        except Zone.DoesNotExist:
            return Response(
                {"error": "Zone non trouvée"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 