from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from django.utils import timezone

class IAssignmentService(ABC):
    """Interface pour le service d'affectation des jobs"""
    
    @abstractmethod
    def assign_jobs(self, assignment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Affecte les jobs avec date_start et session
        
        Args:
            assignment_data: Données d'affectation contenant job_ids, counting_order, session_id, date_start
            
        Returns:
            Dict[str, Any]: Résultat de l'affectation
        """
        pass
    
    @abstractmethod
    def validate_assignment_data(self, assignment_data: Dict[str, Any]) -> None:
        """
        Valide les données d'affectation
        
        Args:
            assignment_data: Données d'affectation à valider
            
        Raises:
            AssignmentValidationError: Si les données sont invalides
        """
        pass
    
    @abstractmethod
    def can_assign_session_to_counting(self, counting_order: int, count_mode: str) -> bool:
        """
        Vérifie si on peut affecter une session à un comptage
        
        Args:
            counting_order: Ordre du comptage
            count_mode: Mode de comptage
            
        Returns:
            bool: True si l'affectation est autorisée
        """
        pass
    
    @abstractmethod
    def get_assignments_by_session(self, session_id: int) -> List[Any]:
        """
        Récupère toutes les affectations d'une session avec leurs jobs associés
        
        Args:
            session_id: ID de la session (équipe)
            
        Returns:
            List[Any]: Liste des affectations avec leurs jobs
            
        Raises:
            AssignmentValidationError: Si la session n'existe pas
        """
        pass

class IAssignmentRepository(ABC):
    """Interface pour le repository d'affectation des jobs"""
    
    @abstractmethod
    def get_jobs_by_ids(self, job_ids: List[int]) -> List[Any]:
        """
        Récupère les jobs par leurs IDs
        
        Args:
            job_ids: Liste des IDs des jobs
            
        Returns:
            List[Any]: Liste des jobs
        """
        pass
    
    @abstractmethod
    def get_counting_by_order_and_inventory(self, order: int, inventory_id: int) -> Optional[Any]:
        """
        Récupère un comptage par ordre et inventaire
        
        Args:
            order: Ordre du comptage
            inventory_id: ID de l'inventaire
            
        Returns:
            Optional[Any]: Le comptage ou None
        """
        pass
    
    @abstractmethod
    def create_assignment(self, assignment_data: Dict[str, Any]) -> Any:
        """
        Crée une nouvelle affectation
        
        Args:
            assignment_data: Données de l'affectation
            
        Returns:
            Any: L'affectation créée
        """
        pass
    
    @abstractmethod
    def update_job_status(self, job_id: int, status: str, date_field: str) -> None:
        """
        Met à jour le statut d'un job
        
        Args:
            job_id: ID du job
            status: Nouveau statut
            date_field: Champ de date à mettre à jour
        """
        pass
    
    @abstractmethod
    def get_existing_assignment_for_job(self, job_id: int) -> Optional[Any]:
        """
        Récupère l'affectation existante pour un job spécifique
        
        Args:
            job_id: ID du job
            
        Returns:
            Optional[Any]: L'affectation existante ou None
        """
        pass
    
    @abstractmethod
    def get_existing_assignment_for_job_and_counting(self, job_id: int, counting_id: int) -> Optional[Any]:
        """
        Récupère l'affectation existante pour un job et un comptage spécifiques
        
        Args:
            job_id: ID du job
            counting_id: ID du comptage
            
        Returns:
            Optional[Any]: L'affectation existante ou None
        """
        pass
    
    @abstractmethod
    def get_assignments_by_session(self, session_id: int) -> List[Any]:
        """
        Récupère toutes les affectations d'une session
        
        Args:
            session_id: ID de la session
            
        Returns:
            List[Any]: Liste des affectations de la session
        """
        pass
    
    @abstractmethod
    def get_assignments_by_session_with_jobs(self, session_id: int) -> List[Any]:
        """
        Récupère toutes les affectations d'une session avec leurs jobs associés
        
        Args:
            session_id: ID de la session (équipe)
            
        Returns:
            List[Any]: Liste des affectations avec leurs jobs (optimisée avec select_related)
        """
        pass 