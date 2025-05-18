"""
Interface pour la gestion des entrepôts.
"""
from abc import ABC, abstractmethod
from typing import List, Any

class IWarehouseRepository(ABC):
    """Interface pour le repository des entrepôts."""
    
    @abstractmethod
    def get_by_id(self, warehouse_id: int) -> Any:
        """Récupère un entrepôt par son ID."""
        pass
    
    @abstractmethod
    def get_all(self) -> List[Any]:
        """Récupère tous les entrepôts."""
        pass
    
    @abstractmethod
    def get_by_inventory_id(self, inventory_id: int) -> List[Any]:
        """Récupère tous les entrepôts associés à un inventaire."""
        pass 