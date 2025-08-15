from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class IResourceAssignmentService(ABC):
    """Interface pour le service d'affectation des ressources aux jobs"""
    
    @abstractmethod
    def assign_resources_to_job(self, assignment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Affecte des ressources à un job
        
        Args:
            assignment_data: Données d'affectation contenant job_id, resource_ids, quantities
            
        Returns:
            Dict[str, Any]: Résultat de l'affectation
        """
        pass
    
    @abstractmethod
    def validate_resource_assignment_data(self, assignment_data: Dict[str, Any]) -> None:
        """
        Valide les données d'affectation des ressources
        
        Args:
            assignment_data: Données d'affectation à valider
            
        Raises:
            ResourceAssignmentValidationError: Si les données sont invalides
        """
        pass
    
    @abstractmethod
    def get_job_resources(self, job_id: int) -> List[Dict[str, Any]]:
        """
        Récupère les ressources affectées à un job
        
        Args:
            job_id: ID du job
            
        Returns:
            List[Dict[str, Any]]: Liste des ressources affectées
        """
        pass
    
    @abstractmethod
    def remove_resources_from_job(self, job_id: int, resource_ids: List[int]) -> Dict[str, Any]:
        """
        Supprime des ressources d'un job
        
        Args:
            job_id: ID du job
            resource_ids: Liste des IDs des ressources à supprimer
            
        Returns:
            Dict[str, Any]: Résultat de la suppression
        """
        pass

class IResourceAssignmentRepository(ABC):
    """Interface pour le repository d'affectation des ressources aux jobs"""
    
    @abstractmethod
    def get_job_by_id(self, job_id: int) -> Optional[Any]:
        """
        Récupère un job par son ID
        
        Args:
            job_id: ID du job
            
        Returns:
            Optional[Any]: Le job ou None s'il n'existe pas
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
    def get_existing_job_resource(self, job_id: int, resource_id: int) -> Optional[Any]:
        """
        Récupère une affectation ressource-job existante
        
        Args:
            job_id: ID du job
            resource_id: ID de la ressource
            
        Returns:
            Optional[Any]: L'affectation existante ou None
        """
        pass
    
    @abstractmethod
    def create_job_resource(self, assignment_data: Dict[str, Any]) -> Any:
        """
        Crée une nouvelle affectation ressource-job
        
        Args:
            assignment_data: Données de l'affectation
            
        Returns:
            Any: L'affectation créée
        """
        pass
    
    @abstractmethod
    def update_job_resource(self, job_resource: Any, **kwargs) -> None:
        """
        Met à jour une affectation ressource-job
        
        Args:
            job_resource: L'affectation à mettre à jour
            **kwargs: Champs à mettre à jour
        """
        pass
    
    @abstractmethod
    def get_job_resources(self, job_id: int) -> List[Any]:
        """
        Récupère les ressources affectées à un job
        
        Args:
            job_id: ID du job
            
        Returns:
            List[Any]: Liste des objets JobDetailRessource
        """
        pass
    
    @abstractmethod
    def delete_job_resources(self, job_id: int, resource_ids: List[int]) -> int:
        """
        Supprime des affectations ressource-job
        
        Args:
            job_id: ID du job
            resource_ids: Liste des IDs des ressources
            
        Returns:
            int: Nombre d'affectations supprimées
        """
        pass 