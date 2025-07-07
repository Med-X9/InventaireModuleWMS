from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from django.db import transaction

class JobRepositoryInterface(ABC):
    """
    Interface pour les opérations de repository des jobs (niveau données)
    """
    
    @abstractmethod
    def create_job(self, **kwargs) -> Any:
        """Crée un job"""
        pass
    
    @abstractmethod
    def create_job_detail(self, **kwargs) -> Any:
        """Crée un job detail"""
        pass
    
    @abstractmethod
    def create_assignment(self, **kwargs) -> Any:
        """Crée un assignment"""
        pass
    
    @abstractmethod
    def get_inventory_by_id(self, inventory_id: int) -> Optional[Any]:
        """Récupère un inventaire par ID"""
        pass
    
    @abstractmethod
    def get_warehouse_by_id(self, warehouse_id: int) -> Optional[Any]:
        """Récupère un warehouse par ID"""
        pass
    
    @abstractmethod
    def get_location_by_id(self, location_id: int) -> Optional[Any]:
        """Récupère un emplacement par ID"""
        pass
    
    @abstractmethod
    def get_countings_by_inventory(self, inventory: Any) -> List[Any]:
        """Récupère les comptages d'un inventaire"""
        pass
    
    @abstractmethod
    def get_job_by_id(self, job_id: int) -> Optional[Any]:
        """Récupère un job par ID"""
        pass
    
    @abstractmethod
    def get_jobs_by_warehouse(self, warehouse_id: int) -> List[Any]:
        """Récupère tous les jobs d'un warehouse"""
        pass
    
    @abstractmethod
    def get_jobs_by_inventory(self, inventory_id: int) -> List[Any]:
        """Récupère tous les jobs d'un inventaire"""
        pass
    
    @abstractmethod
    def get_pending_jobs_by_warehouse(self, warehouse_id: int) -> List[Dict[str, Any]]:
        """Récupère les jobs en attente d'un warehouse"""
        pass
    
    @abstractmethod
    def get_job_details_by_job(self, job: Any) -> List[Any]:
        """Récupère les job details d'un job"""
        pass
    
    @abstractmethod
    def get_job_details_by_job_and_locations(self, job: Any, location_ids: List[int]) -> List[Any]:
        """Récupère les job details d'un job pour des emplacements spécifiques"""
        pass
    
    @abstractmethod
    def get_existing_job_detail_by_location_and_inventory(self, location: Any, inventory: Any) -> Optional[Any]:
        """Récupère un job detail existant pour un emplacement et un inventaire"""
        pass
    
    @abstractmethod
    def get_existing_job_detail_by_location_and_job(self, location: Any, job: Any) -> Optional[Any]:
        """Récupère un job detail existant pour un emplacement et un job"""
        pass
    
    @abstractmethod
    def get_existing_job_detail_by_location_and_inventory_exclude_job(self, location: Any, inventory: Any, job: Any) -> Optional[Any]:
        """Récupère un job detail existant pour un emplacement et un inventaire, en excluant un job"""
        pass
    
    @abstractmethod
    def get_jobs_by_ids(self, job_ids: List[int]) -> List[Any]:
        """Récupère des jobs par leurs IDs"""
        pass
    
    @abstractmethod
    def get_assignments_by_job(self, job: Any) -> List[Any]:
        """Récupère les assignments d'un job"""
        pass
    
    @abstractmethod
    def delete_job_details(self, job_details: List[Any]) -> int:
        """Supprime des job details et retourne le nombre supprimé"""
        pass
    
    @abstractmethod
    def delete_assignments_by_job(self, job: Any) -> int:
        """Supprime tous les assignments d'un job"""
        pass
    
    @abstractmethod
    def delete_job_details_by_job(self, job: Any) -> int:
        """Supprime tous les job details d'un job"""
        pass
    
    @abstractmethod
    def delete_job(self, job: Any) -> None:
        """Supprime un job"""
        pass
    
    @abstractmethod
    def update_job_status(self, job: Any, status: str, **kwargs) -> None:
        """Met à jour le statut d'un job"""
        pass
    
    @abstractmethod
    def get_jobs_with_filters(self, warehouse_id: int, filters: Optional[Dict[str, Any]] = None) -> List[Any]:
        """Récupère des jobs avec filtres"""
        pass

class JobServiceInterface(ABC):
    """
    Interface pour les opérations de service des jobs (niveau métier)
    """
    
    @abstractmethod
    @transaction.atomic
    def create_jobs_for_inventory_warehouse(self, inventory_id: int, warehouse_id: int, emplacements: List[int]) -> List[Any]:
        """
        Crée un job pour un inventaire et un warehouse avec les emplacements spécifiés
        
        Args:
            inventory_id: ID de l'inventaire
            warehouse_id: ID du warehouse
            emplacements: Liste des IDs des emplacements
            
        Returns:
            Liste des jobs créés
            
        Raises:
            JobCreationError: Si une erreur survient lors de la création
        """
        pass
    
    @abstractmethod
    def get_pending_jobs_references(self, warehouse_id: int) -> List[Dict[str, Any]]:
        """
        Récupère les références des jobs en attente pour un warehouse
        
        Args:
            warehouse_id: ID du warehouse
            
        Returns:
            Liste des jobs en attente avec leurs références
            
        Raises:
            JobCreationError: Si une erreur survient
        """
        pass
    
    @abstractmethod
    @transaction.atomic
    def remove_job_emplacements(self, job_id: int, emplacement_id: int) -> Dict[str, Any]:
        """
        Supprime un emplacement d'un job
        
        Args:
            job_id: ID du job
            emplacement_id: ID de l'emplacement à supprimer
            
        Returns:
            Informations sur la suppression
            
        Raises:
            JobCreationError: Si une erreur survient
        """
        pass
    
    @abstractmethod
    @transaction.atomic
    def add_job_emplacements(self, job_id: int, emplacement_ids: List[int]) -> Dict[str, Any]:
        """
        Ajoute des emplacements à un job
        
        Args:
            job_id: ID du job
            emplacement_ids: Liste des IDs des emplacements à ajouter
            
        Returns:
            Informations sur l'ajout
            
        Raises:
            JobCreationError: Si une erreur survient
        """
        pass
    
    @abstractmethod
    @transaction.atomic
    def delete_job(self, job_id: int) -> Dict[str, Any]:
        """
        Supprime définitivement un job
        
        Args:
            job_id: ID du job à supprimer
            
        Returns:
            Informations sur la suppression
            
        Raises:
            JobCreationError: Si une erreur survient
        """
        pass
    
    @abstractmethod
    @transaction.atomic
    def validate_jobs(self, job_ids: List[int]) -> Dict[str, Any]:
        """
        Valide des jobs en changeant leur statut de "EN ATTENTE" à "VALIDE"
        
        Args:
            job_ids: Liste des IDs des jobs à valider
            
        Returns:
            Informations sur la validation
            
        Raises:
            JobCreationError: Si une erreur survient
        """
        pass
    
    @abstractmethod
    def get_jobs_by_warehouse(self, warehouse_id: int, filters: Optional[Dict[str, Any]] = None) -> List[Any]:
        """
        Récupère les jobs d'un warehouse avec filtres optionnels
        
        Args:
            warehouse_id: ID du warehouse
            filters: Dictionnaire de filtres optionnels
            
        Returns:
            Liste des jobs filtrés
        """
        pass
    
    @abstractmethod
    def get_job_by_id(self, job_id: int) -> Optional[Any]:
        """
        Récupère un job par son ID
        
        Args:
            job_id: ID du job
            
        Returns:
            Le job ou None s'il n'existe pas
        """
        pass
    
    @abstractmethod
    def get_jobs_by_inventory(self, inventory_id: int) -> List[Any]:
        """
        Récupère tous les jobs d'un inventaire
        
        Args:
            inventory_id: ID de l'inventaire
            
        Returns:
            Liste des jobs de l'inventaire
        """
        pass
    
    @abstractmethod
    @transaction.atomic
    def delete_multiple_jobs(self, job_ids: List[int]) -> Dict[str, Any]:
        """
        Supprime définitivement plusieurs jobs dans une transaction
        Si un seul job ne peut pas être supprimé, toute l'opération est annulée
        
        Args:
            job_ids: Liste des IDs des jobs à supprimer
            
        Returns:
            Informations sur la suppression
            
        Raises:
            JobCreationError: Si une erreur survient
        """
        pass 