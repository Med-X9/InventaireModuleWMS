from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from django.db import models

class IStockService(ABC):
    """Interface pour le service de stock."""
    @abstractmethod
    def import_stocks_from_excel(self, inventory_id: int, excel_file) -> Dict[str, Any]:
        """Importe des stocks depuis un fichier Excel avec validation."""
        pass

    @abstractmethod
    def validate_stock_data(self, data: Dict[str, Any]) -> List[str]:
        """Valide les données d'un stock."""
        pass

    @abstractmethod
    def create_stock(self, data: Dict[str, Any]) -> models.Model:
        """Crée un nouveau stock."""
        pass

class IStockRepository(ABC):
    """Interface pour le repository de stock."""
    @abstractmethod
    def create(self, stock_data: Dict[str, Any]) -> Any:
        """Crée un nouveau stock."""
        pass

    @abstractmethod
    def get_by_inventory_id(self, inventory_id: int) -> List[Any]:
        """Récupère tous les stocks d'un inventaire."""
        pass

    @abstractmethod
    def bulk_create(self, stocks_data: List[Dict[str, Any]]) -> List[Any]:
        """Crée plusieurs stocks en masse."""
        pass 