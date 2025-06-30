from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from django.db import models

class IInventoryService(ABC):
    """Interface pour le service d'inventaire."""
    @abstractmethod
    def create_inventory(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée un nouvel inventaire."""
        pass

    @abstractmethod
    def update_inventory(self, inventory_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Met à jour un inventaire existant."""
        pass

    @abstractmethod
    def get_inventory_by_id(self, inventory_id: int) -> Any:
        """Récupère un inventaire par son ID."""
        pass

    @abstractmethod
    def get_inventory_detail(self, inventory_id: int) -> Any:
        """Récupère un inventaire avec toutes ses données associées."""
        pass

    @abstractmethod
    def get_inventory_list(self, filters_dict: Dict[str, Any] = None, ordering: str = '-date', page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """Récupère la liste des inventaires avec filtres, tri et pagination."""
        pass

    @abstractmethod
    def validate_inventory_data(self, data: Dict[str, Any]) -> None:
        """Valide les données d'un inventaire."""
        pass

    @abstractmethod
    def delete_inventory(self, inventory_id: int) -> None:
        """Supprime complètement un inventaire et tous ses enregistrements liés."""
        pass

    @abstractmethod
    def soft_delete_inventory(self, inventory_id: int) -> None:
        """Effectue un soft delete d'un inventaire."""
        pass

    @abstractmethod
    def restore_inventory(self, inventory_id: int) -> None:
        """Restaure un inventaire qui a été soft delete."""
        pass

    @abstractmethod
    def validate_counting_modes(self, comptages: List[Dict[str, Any]]) -> List[str]:
        """Valide les modes de comptage."""
        pass

    @abstractmethod
    def launch_inventory(self, inventory_id: int) -> None:
        """Lance un inventaire."""
        pass

    @abstractmethod
    def cancel_inventory(self, inventory_id: int) -> None:
        """Annule le lancement d'un inventaire."""
        pass

class IInventoryRepository(ABC):
    """
    Interface pour le repository d'inventaire
    """
    @abstractmethod
    def get_all(self) -> List[Any]:
        """
        Récupère tous les inventaires
        """
        pass

    @abstractmethod
    def get_by_id(self, inventory_id: int) -> Any:
        """
        Récupère un inventaire par son ID
        """
        pass

    @abstractmethod
    def get_by_filters(self, filters_dict: Dict[str, Any]) -> List[Any]:
        """
        Récupère les inventaires selon les filtres
        """
        pass

    @abstractmethod
    def create(self, inventory_data: Dict[str, Any]) -> Any:
        """
        Crée un nouvel inventaire
        """
        pass

    @abstractmethod
    def update(self, inventory_id: int, inventory_data: Dict[str, Any]) -> Any:
        """
        Met à jour un inventaire
        """
        pass

    @abstractmethod
    def delete(self, inventory_id: int) -> None:
        """
        Supprime un inventaire
        """
        pass

    @abstractmethod
    def get_with_related_data(self, inventory_id: int) -> Any:
        """
        Récupère un inventaire avec ses données associées
        """
        pass 