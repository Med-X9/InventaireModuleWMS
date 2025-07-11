"""
Repository pour la gestion des stocks.
"""
import logging
from typing import List, Dict, Any, Optional
from django.db import transaction
from django.db.models import Q
from apps.masterdata.models import Stock, Product, Location, UnitOfMeasure
from ..exceptions import StockNotFoundError, StockValidationError

logger = logging.getLogger(__name__)


class StockRepository:
    """
    Repository pour la gestion des stocks.
    Gère toutes les opérations de base de données liées aux stocks.
    """
    
    def __init__(self):
        self.model = Stock
    
    def create(self, data: Dict[str, Any]) -> Stock:
        """
        Crée un nouveau stock.
        
        Args:
            data: Les données du stock
            
        Returns:
            Stock: Le stock créé
            
        Raises:
            StockValidationError: Si les données sont invalides
        """
        try:
            stock = Stock.objects.create(**data)
            logger.info(f"Stock créé avec succès: ID {stock.id}")
            return stock
        except Exception as e:
            logger.error(f"Erreur lors de la création du stock: {str(e)}")
            raise StockValidationError(f"Erreur lors de la création du stock: {str(e)}")
    
    def get_by_id(self, stock_id: int) -> Stock:
        """
        Récupère un stock par son ID.
        
        Args:
            stock_id: L'ID du stock
            
        Returns:
            Stock: Le stock trouvé
            
        Raises:
            StockNotFoundError: Si le stock n'existe pas
        """
        try:
            stock = Stock.objects.get(id=stock_id)
            return stock
        except Stock.DoesNotExist:
            raise StockNotFoundError(f"Stock avec l'ID {stock_id} non trouvé")
    
    def get_by_inventory_id(self, inventory_id: int) -> List[Stock]:
        """
        Récupère tous les stocks d'un inventaire.
        
        Args:
            inventory_id: L'ID de l'inventaire
            
        Returns:
            List[Stock]: Liste des stocks de l'inventaire
        """
        return Stock.objects.filter(inventory_id=inventory_id).select_related(
            'product', 'location', 'unit_of_measure'
        )
    
    def get_by_filters(self, filters: Dict[str, Any]) -> List[Stock]:
        """
        Récupère des stocks selon des filtres.
        
        Args:
            filters: Dictionnaire de filtres
            
        Returns:
            List[Stock]: Liste des stocks filtrés
        """
        queryset = Stock.objects.all().select_related(
            'product', 'location', 'unit_of_measure', 'inventory'
        )
        
        # Appliquer les filtres
        if 'inventory_id' in filters:
            queryset = queryset.filter(inventory_id=filters['inventory_id'])
        
        if 'product_id' in filters:
            queryset = queryset.filter(product_id=filters['product_id'])
        
        if 'location_id' in filters:
            queryset = queryset.filter(location_id=filters['location_id'])
        
        if 'quantity_min' in filters:
            queryset = queryset.filter(quantity_available__gte=filters['quantity_min'])
        
        if 'quantity_max' in filters:
            queryset = queryset.filter(quantity_available__lte=filters['quantity_max'])
        
        if 'search' in filters:
            search_term = filters['search']
            queryset = queryset.filter(
                Q(product__product_name__icontains=search_term) |
                Q(product__Internal_Product_Code__icontains=search_term) |
                Q(location__location_name__icontains=search_term) |
                Q(location__location_reference__icontains=search_term)
            )
        
        return queryset
    
    def update(self, stock_id: int, data: Dict[str, Any]) -> Stock:
        """
        Met à jour un stock existant.
        
        Args:
            stock_id: L'ID du stock
            data: Les nouvelles données du stock
            
        Returns:
            Stock: Le stock mis à jour
            
        Raises:
            StockNotFoundError: Si le stock n'existe pas
            StockValidationError: Si les données sont invalides
        """
        try:
            stock = self.get_by_id(stock_id)
            
            # Mettre à jour les champs
            for field, value in data.items():
                if hasattr(stock, field):
                    setattr(stock, field, value)
            
            stock.save()
            logger.info(f"Stock {stock_id} mis à jour avec succès")
            return stock
            
        except StockNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du stock {stock_id}: {str(e)}")
            raise StockValidationError(f"Erreur lors de la mise à jour du stock: {str(e)}")
    
    def delete(self, stock_id: int) -> bool:
        """
        Supprime un stock.
        
        Args:
            stock_id: L'ID du stock
            
        Returns:
            bool: True si la suppression a réussi
            
        Raises:
            StockNotFoundError: Si le stock n'existe pas
        """
        try:
            stock = self.get_by_id(stock_id)
            stock.delete()
            logger.info(f"Stock {stock_id} supprimé avec succès")
            return True
        except StockNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du stock {stock_id}: {str(e)}")
            raise StockValidationError(f"Erreur lors de la suppression du stock: {str(e)}")
    
    def delete_by_inventory_id(self, inventory_id: int) -> int:
        """
        Supprime tous les stocks d'un inventaire.
        
        Args:
            inventory_id: L'ID de l'inventaire
            
        Returns:
            int: Nombre de stocks supprimés
        """
        try:
            deleted_count, _ = Stock.objects.filter(inventory_id=inventory_id).delete()
            logger.info(f"{deleted_count} stocks supprimés pour l'inventaire {inventory_id}")
            return deleted_count
        except Exception as e:
            logger.error(f"Erreur lors de la suppression des stocks de l'inventaire {inventory_id}: {str(e)}")
            raise StockValidationError(f"Erreur lors de la suppression des stocks: {str(e)}")
    
    def bulk_create(self, stocks_data: List[Dict[str, Any]]) -> List[Stock]:
        """
        Crée plusieurs stocks en lot.
        
        Args:
            stocks_data: Liste des données des stocks
            
        Returns:
            List[Stock]: Liste des stocks créés
        """
        try:
            stocks = []
            for data in stocks_data:
                stock = Stock(**data)
                stocks.append(stock)
            
            created_stocks = Stock.objects.bulk_create(stocks)
            logger.info(f"{len(created_stocks)} stocks créés en lot")
            return created_stocks
            
        except Exception as e:
            logger.error(f"Erreur lors de la création en lot des stocks: {str(e)}")
            raise StockValidationError(f"Erreur lors de la création en lot des stocks: {str(e)}")
    
    def bulk_update(self, stocks: List[Stock], fields: List[str]) -> int:
        """
        Met à jour plusieurs stocks en lot.
        
        Args:
            stocks: Liste des stocks à mettre à jour
            fields: Liste des champs à mettre à jour
            
        Returns:
            int: Nombre de stocks mis à jour
        """
        try:
            updated_count = Stock.objects.bulk_update(stocks, fields)
            logger.info(f"{updated_count} stocks mis à jour en lot")
            return updated_count
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour en lot des stocks: {str(e)}")
            raise StockValidationError(f"Erreur lors de la mise à jour en lot des stocks: {str(e)}")
    
    def get_stock_summary(self, inventory_id: int) -> Dict[str, Any]:
        """
        Récupère un résumé des stocks d'un inventaire.
        
        Args:
            inventory_id: L'ID de l'inventaire
            
        Returns:
            Dict[str, Any]: Résumé des stocks
        """
        try:
            stocks = self.get_by_inventory_id(inventory_id)
            
            summary = {
                'total_stocks': len(stocks),
                'total_quantity': sum(stock.quantity_available for stock in stocks),
                'unique_products': len(set(stock.product_id for stock in stocks if stock.product_id)),
                'unique_locations': len(set(stock.location_id for stock in stocks if stock.location_id)),
                'products_with_stock': len([s for s in stocks if s.quantity_available > 0]),
                'empty_locations': len([s for s in stocks if s.quantity_available == 0])
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul du résumé des stocks pour l'inventaire {inventory_id}: {str(e)}")
            raise StockValidationError(f"Erreur lors du calcul du résumé des stocks: {str(e)}")
    
    def check_stock_exists(self, inventory_id: int, product_id: int, location_id: int) -> bool:
        """
        Vérifie si un stock existe déjà pour un inventaire, produit et emplacement donnés.
        
        Args:
            inventory_id: L'ID de l'inventaire
            product_id: L'ID du produit
            location_id: L'ID de l'emplacement
            
        Returns:
            bool: True si le stock existe
        """
        return Stock.objects.filter(
            inventory_id=inventory_id,
            product_id=product_id,
            location_id=location_id
        ).exists() 