"""
Interfaces pour l'application inventory.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from django.db import models

class IInventoryService(ABC):
    """Interface pour le service d'inventaire."""
    
    @abstractmethod
    def create_inventory(self, data: Dict[str, Any]) -> models.Model:
        """Crée un nouvel inventaire."""
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
    """Interface pour le repository d'inventaire."""
    
    @abstractmethod
    def get_by_id(self, inventory_id: int) -> models.Model:
        """Récupère un inventaire par son ID."""
        pass
    
    @abstractmethod
    def get_all(self) -> List[models.Model]:
        """Récupère tous les inventaires."""
        pass 