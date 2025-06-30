from typing import List, Dict, Any
from django.db import transaction
from ..interfaces.stock_interface import IStockRepository
from apps.masterdata.models import Stock, Location, Product
from ..models import Inventory

class StockRepository(IStockRepository):
    """Repository pour la gestion des stocks."""
    
    def create(self, stock_data: Dict[str, Any]) -> Stock:
        """
        Crée un nouveau stock.
        
        Args:
            stock_data: Les données du stock
            
        Returns:
            Stock: Le stock créé
        """
        return Stock.objects.create(**stock_data)
    
    def get_by_inventory_id(self, inventory_id: int) -> List[Stock]:
        """
        Récupère tous les stocks d'un inventaire.
        
        Args:
            inventory_id: L'ID de l'inventaire
            
        Returns:
            List[Stock]: Liste des stocks de l'inventaire
        """
        return Stock.objects.filter(inventory_id=inventory_id)
    
    def bulk_create(self, stocks_data: List[Dict[str, Any]]) -> List[Stock]:
        """
        Crée plusieurs stocks en masse.
        
        Args:
            stocks_data: Liste des données des stocks
            
        Returns:
            List[Stock]: Liste des stocks créés
        """
        stocks = []
        for stock_data in stocks_data:
            # Créer individuellement pour que le CodeGeneratorMixin génère la référence
            stock = Stock.objects.create(**stock_data)
            stocks.append(stock)
        
        return stocks
    
    def delete_by_inventory_id(self, inventory_id: int) -> int:
        """
        Supprime tous les stocks d'un inventaire.
        
        Args:
            inventory_id: L'ID de l'inventaire
            
        Returns:
            int: Nombre de stocks supprimés
        """
        count, _ = Stock.objects.filter(inventory_id=inventory_id).delete()
        return count 