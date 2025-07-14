"""
Interface pour le service de gestion des stocks.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from django.core.files.uploadedfile import UploadedFile
from apps.masterdata.models import Stock


class IStockService(ABC):
    """
    Interface pour le service de gestion des stocks.
    Définit les méthodes que doit implémenter le service de stocks.
    """
    
    @abstractmethod
    def import_stocks_from_excel(self, inventory_id: int, excel_file: UploadedFile) -> Dict[str, Any]:
        """
        Importe des stocks depuis un fichier Excel avec validation.
        
        Args:
            inventory_id: L'ID de l'inventaire
            excel_file: Le fichier Excel à importer
            
        Returns:
            Dict[str, Any]: Résultat de l'import avec succès/erreurs
            
        Raises:
            InventoryNotFoundError: Si l'inventaire n'existe pas
            StockValidationError: Si le fichier est invalide
        """
        pass
    
    @abstractmethod
    def validate_stock_data(self, data: Dict[str, Any]) -> List[str]:
        """
        Valide les données d'un stock.
        
        Args:
            data: Les données du stock
            
        Returns:
            List[str]: Liste des erreurs de validation
        """
        pass
    
    @abstractmethod
    def create_stock(self, data: Dict[str, Any]) -> Stock:
        """
        Crée un nouveau stock.
        
        Args:
            data: Les données du stock
            
        Returns:
            Stock: Le stock créé
        """
        pass
    
    @abstractmethod
    def get_stocks_by_inventory(self, inventory_id: int) -> List[Stock]:
        """
        Récupère tous les stocks d'un inventaire.
        
        Args:
            inventory_id: L'ID de l'inventaire
            
        Returns:
            List[Stock]: Liste des stocks de l'inventaire
        """
        pass
    
    @abstractmethod
    def update_stock(self, stock_id: int, data: Dict[str, Any]) -> Stock:
        """
        Met à jour un stock existant.
        
        Args:
            stock_id: L'ID du stock
            data: Les nouvelles données du stock
            
        Returns:
            Stock: Le stock mis à jour
        """
        pass
    
    @abstractmethod
    def delete_stock(self, stock_id: int) -> bool:
        """
        Supprime un stock.
        
        Args:
            stock_id: L'ID du stock
            
        Returns:
            bool: True si la suppression a réussi
        """
        pass
    
    @abstractmethod
    def bulk_create_stocks(self, stocks_data: List[Dict[str, Any]]) -> List[Stock]:
        """
        Crée plusieurs stocks en lot.
        
        Args:
            stocks_data: Liste des données des stocks
            
        Returns:
            List[Stock]: Liste des stocks créés
        """
        pass
    
    @abstractmethod
    def delete_stocks_by_inventory(self, inventory_id: int) -> int:
        """
        Supprime tous les stocks d'un inventaire.
        
        Args:
            inventory_id: L'ID de l'inventaire
            
        Returns:
            int: Nombre de stocks supprimés
        """
        pass 