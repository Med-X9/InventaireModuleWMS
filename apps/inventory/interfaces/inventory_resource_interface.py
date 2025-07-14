from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class IInventoryResourceService(ABC):
    """Interface pour le service d'affectation des ressources aux inventaires"""
    
    @abstractmethod
    def assign_resources_to_inventory(self, inventory_id: int, assignment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Affecte des ressources à un inventaire
        
        Args:
            inventory_id: ID de l'inventaire
            assignment_data: Données d'affectation contenant resource_assignments
            
        Returns:
            Dict[str, Any]: Résultat de l'affectation
        """
        pass
    
    @abstractmethod
    def get_inventory_resources(self, inventory_id: int) -> List[Any]:
        """
        Récupère les ressources affectées à un inventaire
        
        Args:
            inventory_id: ID de l'inventaire
            
        Returns:
            List[Any]: Liste des objets InventoryDetailRessource
        """
        pass
    
    @abstractmethod
    def remove_resources_from_inventory(self, inventory_id: int, resource_ids: List[int]) -> Dict[str, Any]:
        """
        Supprime des ressources d'un inventaire
        
        Args:
            inventory_id: ID de l'inventaire
            resource_ids: Liste des IDs des ressources à supprimer
            
        Returns:
            Dict[str, Any]: Résultat de la suppression
        """
        pass

class IInventoryResourceRepository(ABC):
    """Interface pour le repository d'affectation des ressources aux inventaires"""
    
    @abstractmethod
    def get_inventory_by_id(self, inventory_id: int) -> Optional[Any]:
        """
        Récupère un inventaire par son ID
        
        Args:
            inventory_id: ID de l'inventaire
            
        Returns:
            Optional[Any]: L'inventaire ou None s'il n'existe pas
        """
        pass
    
    @abstractmethod
    def get_resource_by_id(self, resource_id: int) -> Optional[Any]:
        """
        Récupère une ressource par son ID
        
        Args:
            resource_id: ID de la ressource
            
        Returns:
            Optional[Any]: La ressource ou None si elle n'existe pas
        """
        pass
    
    @abstractmethod
    def get_existing_inventory_resource(self, inventory_id: int, resource_id: int) -> Optional[Any]:
        """
        Récupère une affectation ressource-inventaire existante
        
        Args:
            inventory_id: ID de l'inventaire
            resource_id: ID de la ressource
            
        Returns:
            Optional[Any]: L'affectation existante ou None
        """
        pass
    
    @abstractmethod
    def create_inventory_resource(self, assignment_data: Dict[str, Any]) -> Any:
        """
        Crée une nouvelle affectation ressource-inventaire
        
        Args:
            assignment_data: Données de l'affectation
            
        Returns:
            Any: L'affectation créée
        """
        pass
    
    @abstractmethod
    def update_inventory_resource(self, inventory_resource: Any, **kwargs) -> None:
        """
        Met à jour une affectation ressource-inventaire
        
        Args:
            inventory_resource: L'affectation à mettre à jour
            **kwargs: Champs à mettre à jour
        """
        pass
    
    @abstractmethod
    def get_inventory_resources(self, inventory_id: int) -> List[Any]:
        """
        Récupère toutes les ressources affectées à un inventaire
        
        Args:
            inventory_id: ID de l'inventaire
            
        Returns:
            List[Any]: Liste des affectations ressource-inventaire
        """
        pass
    
    @abstractmethod
    def delete_inventory_resources(self, inventory_id: int, resource_ids: List[int]) -> int:
        """
        Supprime des affectations ressource-inventaire
        
        Args:
            inventory_id: ID de l'inventaire
            resource_ids: Liste des IDs des ressources
            
        Returns:
            int: Nombre d'affectations supprimées
        """
        pass 