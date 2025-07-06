from typing import List, Any, Optional
from ..interfaces.ressource_interface import IRessourceRepository
from apps.masterdata.models import Ressource, TypeRessource

class RessourceRepository(IRessourceRepository):
    """
    Repository pour la gestion des ressources
    """
    
    def get_all_resources(self) -> List[Any]:
        """
        Récupère toutes les ressources actives
        """
        return list(Ressource.objects.filter(
            status='ACTIVE', 
            is_deleted=False
        ).select_related('type_ressource').order_by('libelle'))
    
    def get_resource_by_id(self, resource_id: int) -> Optional[Any]:
        """
        Récupère une ressource par son ID
        """
        try:
            return Ressource.objects.select_related('type_ressource').get(
                id=resource_id, 
                is_deleted=False
            )
        except Ressource.DoesNotExist:
            return None
    
    def get_resources_by_type(self, type_ressource_id: int) -> List[Any]:
        """
        Récupère les ressources par type
        """
        return list(Ressource.objects.filter(
            type_ressource_id=type_ressource_id,
            status='ACTIVE',
            is_deleted=False
        ).select_related('type_ressource').order_by('libelle'))
    
    def get_active_resources(self) -> List[Any]:
        """
        Récupère toutes les ressources actives
        """
        return self.get_all_resources() 