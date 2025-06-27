from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from django.db import transaction

class JobInterface(ABC):
    """
    Interface pour les opérations de gestion des jobs
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
    def remove_job_emplacements(self, job_id: int, emplacement_ids: List[int]) -> Dict[str, Any]:
        """
        Supprime des emplacements d'un job
        
        Args:
            job_id: ID du job
            emplacement_ids: Liste des IDs des emplacements à supprimer
            
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