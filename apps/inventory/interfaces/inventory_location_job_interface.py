from abc import ABC, abstractmethod
from typing import Any, List, Dict

class IInventoryLocationJobRepository(ABC):
    """Interface pour le repository InventoryLocationJob"""
    
    @abstractmethod
    def create(self, data: Dict[str, Any]) -> Any:
        """Crée un nouvel InventoryLocationJob"""
        pass
    
    @abstractmethod
    def bulk_create(self, data_list: List[Dict[str, Any]]) -> List[Any]:
        """Crée plusieurs InventoryLocationJob en une seule opération"""
        pass
    
    @abstractmethod
    def get_by_inventory_id(self, inventory_id: int) -> List[Any]:
        """Récupère tous les InventoryLocationJob pour un inventaire"""
        pass
    
    @abstractmethod
    def delete_by_inventory_id(self, inventory_id: int) -> int:
        """Supprime tous les InventoryLocationJob pour un inventaire"""
        pass

