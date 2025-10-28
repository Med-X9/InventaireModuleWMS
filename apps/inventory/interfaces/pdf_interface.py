"""
Interface pour la génération de PDF des jobs d'inventaire
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from io import BytesIO

class PDFRepositoryInterface(ABC):
    """Interface pour le repository PDF (niveau données)"""
    
    @abstractmethod
    def get_inventory_by_id(self, inventory_id: int) -> Optional[Any]:
        """Récupère un inventaire par ID"""
        pass
    
    @abstractmethod
    def get_counting_by_id(self, counting_id: int) -> Optional[Any]:
        """Récupère un comptage par ID"""
        pass
    
    @abstractmethod
    def get_countings_by_inventory(self, inventory: Any) -> List[Any]:
        """Récupère tous les comptages d'un inventaire"""
        pass
    
    @abstractmethod
    def get_all_jobs_by_inventory(self, inventory: Any) -> List[Any]:
        """Récupère tous les jobs d'un inventaire"""
        pass
    
    @abstractmethod
    def get_jobs_by_counting(self, inventory: Any, counting: Any) -> List[Any]:
        """Récupère les jobs d'un inventaire pour un comptage spécifique"""
        pass
    
    @abstractmethod
    def get_job_details_by_job(self, job: Any) -> List[Any]:
        """Récupère les job details d'un job"""
        pass
    
    @abstractmethod
    def get_stocks_by_location_and_inventory(self, location: Any, inventory: Any) -> List[Any]:
        """Récupère les stocks d'un emplacement pour un inventaire"""
        pass
    
    @abstractmethod
    def get_assignments_by_job(self, job: Any) -> List[Any]:
        """Récupère les assignments d'un job"""
        pass


class PDFServiceInterface(ABC):
    """Interface pour le service PDF (niveau métier)"""
    
    @abstractmethod
    def generate_inventory_jobs_pdf(self, inventory_id: int, counting_id: Optional[int] = None) -> BytesIO:
        """
        Génère un PDF des jobs d'un inventaire
        
        Args:
            inventory_id: ID de l'inventaire
            counting_id: ID du comptage (optionnel)
            
        Returns:
            BytesIO: Le contenu du PDF en mémoire
            
        Raises:
            Exception: Si une erreur survient
        """
        pass


class PDFUseCaseInterface(ABC):
    """Interface pour le usecase PDF (orchestration)"""
    
    @abstractmethod
    def execute(self, inventory_id: int, counting_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Exécute la génération du PDF des jobs d'inventaire
        
        Args:
            inventory_id: ID de l'inventaire
            counting_id: ID du comptage (optionnel)
            
        Returns:
            Dict contenant le PDF et les métadonnées
            
        Raises:
            Exception: Si une erreur survient
        """
        pass
