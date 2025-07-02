from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from django.db import models
from ..models import Inventory, Counting

class IInventoryService(ABC):
    """Interface pour le service d'inventaire."""
    @abstractmethod
    def create_inventory(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée un nouvel inventaire."""
        pass

    @abstractmethod
    def get_inventory_by_id(self, inventory_id: int) -> Inventory:
        """Récupère un inventaire par son ID."""
        pass

    @abstractmethod
    def update_inventory(self, inventory_id: int, data: Dict[str, Any]) -> Inventory:
        """Met à jour un inventaire."""
        pass

    @abstractmethod
    def delete_inventory(self, inventory_id: int) -> None:
        """Supprime un inventaire."""
        pass

    @abstractmethod
    def launch_inventory(self, inventory_id: int) -> None:
        """Lance un inventaire."""
        pass

    @abstractmethod
    def cancel_inventory(self, inventory_id: int) -> None:
        """Annule un inventaire."""
        pass

    @abstractmethod
    def validate_inventory_data(self, data: Dict[str, Any]) -> None:
        """Valide les données d'un inventaire."""
        pass

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

class IInventoryUpdateService(ABC):
    """Interface pour le service de mise à jour d'inventaire."""
    
    @abstractmethod
    def update_inventory(self, inventory_id: int, data: Dict[str, Any]) -> Inventory:
        """
        Met à jour un inventaire avec validation complète.
        
        Args:
            inventory_id: L'ID de l'inventaire à mettre à jour
            data: Les nouvelles données de l'inventaire
            
        Returns:
            Inventory: L'inventaire mis à jour
            
        Raises:
            InventoryNotFoundError: Si l'inventaire n'existe pas
            InventoryValidationError: Si les données sont invalides
        """
        pass
    
    @abstractmethod
    def validate_update_data(self, data: Dict[str, Any]) -> None:
        """
        Valide les données de mise à jour.
        
        Args:
            data: Les données à valider
            
        Raises:
            InventoryValidationError: Si les données sont invalides
        """
        pass 