from typing import List, Optional
from ..models import SousZone
from django.db.models import Q

class SousZoneService:
    """
    Service pour la gestion des sous-zones.
    """
    
    def get_sous_zones(self, zone_id: Optional[int] = None, search: Optional[str] = None) -> List[SousZone]:
        """
        Récupère la liste des sous-zones avec filtres optionnels.
        
        Args:
            zone_id: ID de la zone pour filtrer les sous-zones
            search: Terme de recherche pour filtrer par nom de sous-zone
            
        Returns:
            List[SousZone]: Liste des sous-zones correspondant aux critères
        """
        queryset = SousZone.objects.all()
        
        # Filtre par zone si spécifié
        if zone_id:
            queryset = queryset.filter(zone_id=zone_id)
        
        # Filtre par recherche si spécifié
        if search:
            queryset = queryset.filter(
                Q(sous_zone_name__icontains=search) |
                Q(zone__zone_name__icontains=search) |
                Q(zone__warehouse__warehouse_name__icontains=search)
            )
        
        return queryset.select_related('zone', 'zone__warehouse').order_by(
            'zone__warehouse__warehouse_name',
            'zone__zone_name',
            'sous_zone_name'
        ) 