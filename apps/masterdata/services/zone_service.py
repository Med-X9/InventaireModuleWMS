from typing import List, Optional
from ..repositories.zone_repository import ZoneRepository
from django.db.models import Q

class ZoneService:
    """
    Service pour la gestion des zones.
    """
    zone_repo = ZoneRepository()
    
    def get_zones(self, warehouse_id: Optional[int] = None, search: Optional[str] = None) -> List:
        """
        Récupère la liste des zones avec filtres optionnels.
        
        Args:
            warehouse_id: ID de l'entrepôt pour filtrer les zones
            search: Terme de recherche pour filtrer par nom de zone
            
        Returns:
            List[Zone]: Liste des zones correspondant aux critères
        """
        queryset = self.zone_repo.get_all()
        
        # Filtre par entrepôt si spécifié
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)
        
        # Filtre par recherche si spécifié
        if search:
            queryset = queryset.filter(
                Q(zone_name__icontains=search) |
                Q(warehouse__warehouse_name__icontains=search)
            )
        
        return queryset.select_related('warehouse').order_by('warehouse__warehouse_name', 'zone_name') 