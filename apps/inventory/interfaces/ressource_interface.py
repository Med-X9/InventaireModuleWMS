from abc import ABC, abstractmethod
from typing import List, Any, Optional, Dict

class IRessourceRepository(ABC):
    """
    Interface pour le repository des ressources
    """
    
    @abstractmethod
    def get_all_resources(self) -> List[Any]:
        """
        Récupère toutes les ressources actives
        """
        pass
    
    @abstractmethod
    def get_resource_by_id(self, resource_id: int) -> Optional[Any]:
        """
        Récupère une ressource par son ID
        """
        pass
    
    @abstractmethod
    def get_resources_by_type(self, type_ressource_id: int) -> List[Any]:
        """
        Récupère les ressources par type
        """
        pass
    
    @abstractmethod
    def get_active_resources(self) -> List[Any]:
        """
        Récupère toutes les ressources actives
        """
        pass

class IRessourceService(ABC):
    """
    Interface pour le service des ressources
    """
    
    @abstractmethod
    def get_all_resources(self) -> List[Dict[str, Any]]:
        """
        Récupère toutes les ressources avec reference, libelle et type_ressource
        """
        pass
    
    @abstractmethod
    def get_resource_by_id(self, resource_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère une ressource par son ID
        """
        pass
    
    @abstractmethod
    def get_resources_by_type(self, type_ressource_id: int) -> List[Dict[str, Any]]:
        """
        Récupère les ressources par type
        """
        pass 