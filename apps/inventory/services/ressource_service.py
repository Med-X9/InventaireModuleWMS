from typing import List, Dict, Any, Optional
from ..interfaces.ressource_interface import IRessourceService
from ..repositories.ressource_repository import RessourceRepository

class RessourceService(IRessourceService):
    """
    Service pour la gestion des ressources
    """
    
    def __init__(self, repository: RessourceRepository = None):
        self.repository = repository or RessourceRepository()
    
    def get_all_resources(self) -> List[Dict[str, Any]]:
        """
        Récupère toutes les ressources avec id, reference, libelle et type_ressource
        """
        resources = self.repository.get_all_resources()
        return [{
            'id': resource.id,
            'reference': resource.reference,
            'libelle': resource.libelle,
            'type_ressource': resource.type_ressource.libelle if resource.type_ressource else None
        } for resource in resources]
    
    def get_resource_by_id(self, resource_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère une ressource par son ID
        """
        resource = self.repository.get_resource_by_id(resource_id)
        if resource:
            return {
                'id': resource.id,
                'reference': resource.reference,
                'libelle': resource.libelle,
                'type_ressource': resource.type_ressource.libelle if resource.type_ressource else None
            }
        return None
    
    def get_resources_by_type(self, type_ressource_id: int) -> List[Dict[str, Any]]:
        """
        Récupère les ressources par type
        """
        resources = self.repository.get_resources_by_type(type_ressource_id)
        return [{
            'id': resource.id,
            'reference': resource.reference,
            'libelle': resource.libelle,
            'type_ressource': resource.type_ressource.libelle if resource.type_ressource else None
        } for resource in resources] 