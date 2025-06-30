from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from django.db import models

class ICountingService(ABC):
    """Interface pour le service de comptage."""
    @abstractmethod
    def create_counting(self, data: Dict[str, Any]) -> models.Model:
        """Crée un nouveau comptage."""
        pass

    @abstractmethod
    def validate_counting_data(self, data: Dict[str, Any]) -> None:
        """Valide les données d'un comptage."""
        pass

class ICountingRepository(ABC):
    """
    Interface pour le repository de comptages
    """
    @abstractmethod
    def get_all(self) -> List[Any]:
        """
        Récupère tous les comptages
        """
        pass

    @abstractmethod
    def get_by_id(self, counting_id: int) -> Any:
        """
        Récupère un comptage par son ID
        """
        pass

    @abstractmethod
    def get_by_filters(self, filters_dict: Dict[str, Any]) -> List[Any]:
        """
        Récupère les comptages selon les filtres
        """
        pass

    @abstractmethod
    def create(self, counting_data: Dict[str, Any]) -> Any:
        """
        Crée un nouveau comptage
        """
        pass

    @abstractmethod
    def update(self, counting_id: int, counting_data: Dict[str, Any]) -> Any:
        """
        Met à jour un comptage
        """
        pass

    @abstractmethod
    def delete(self, counting_id: int) -> None:
        """
        Supprime un comptage
        """
        pass

    @abstractmethod
    def get_by_inventory_id(self, inventory_id: int) -> List[Any]:
        """
        Récupère tous les comptages d'un inventaire
        """
        pass

    @abstractmethod
    def get_by_count_mode(self, count_mode: str) -> List[Any]:
        """
        Récupère les comptages par mode de comptage
        """
        pass

    @abstractmethod
    def get_with_related_data(self, counting_id: int) -> Any:
        """
        Récupère un comptage avec ses données associées
        """
        pass 