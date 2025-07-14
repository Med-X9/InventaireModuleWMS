"""
Use case pour la validation d'import de stock selon le type d'inventaire.
"""
from typing import Dict, Any, Optional
from django.db import transaction
from ..models import Inventory
from ..repositories import InventoryRepository
from ..repositories.stock_repository import StockRepository
from ..exceptions import InventoryNotFoundError, StockValidationError
from apps.masterdata.models import Stock
import logging

logger = logging.getLogger(__name__)

class StockImportValidationUseCase:
    """
    Use case pour valider l'import de stock selon le type d'inventaire.
    
    Règles métier:
    - Pour un inventaire de type TOURNANT: vérifier s'il y a déjà des stocks importés
    - Pour un inventaire de type GENERAL: pas de restriction
    """
    
    def __init__(self):
        self.inventory_repository = InventoryRepository()
        self.stock_repository = StockRepository()
    
    def validate_stock_import(self, inventory_id: int) -> Dict[str, Any]:
        """
        Valide l'import de stock selon le type d'inventaire.
        
        Args:
            inventory_id: L'ID de l'inventaire
            
        Returns:
            Dict[str, Any]: Résultat de la validation avec les informations nécessaires
            
        Raises:
            InventoryNotFoundError: Si l'inventaire n'existe pas
            StockValidationError: Si l'import n'est pas autorisé
        """
        try:
            # Récupérer l'inventaire
            inventory = self.inventory_repository.get_by_id(inventory_id)
            
            # Vérifier le type d'inventaire
            if inventory.inventory_type == 'TOURNANT':
                return self._validate_tournant_inventory(inventory)
            elif inventory.inventory_type == 'GENERAL':
                return self._validate_general_inventory(inventory)
            else:
                raise StockValidationError(f"Type d'inventaire non supporté: {inventory.inventory_type}")
                
        except InventoryNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la validation d'import de stock: {str(e)}", exc_info=True)
            raise StockValidationError(f"Erreur lors de la validation: {str(e)}")
    
    def _validate_tournant_inventory(self, inventory: Inventory) -> Dict[str, Any]:
        """
        Valide l'import pour un inventaire de type TOURNANT.
        
        Args:
            inventory: L'inventaire à valider
            
        Returns:
            Dict[str, Any]: Résultat de la validation
        """
        # Vérifier s'il y a déjà des stocks importés pour cet inventaire
        existing_stocks_count = Stock.objects.filter(
            inventory_id=inventory.id,
            is_deleted=False
        ).count()
        
        if existing_stocks_count > 0:
            # Il y a déjà des stocks importés
            return {
                'can_import': False,
                'inventory_type': 'TOURNANT',
                'existing_stocks_count': existing_stocks_count,
                'message': (
                    f"Cet inventaire de type TOURNANT a déjà {existing_stocks_count} stocks importés. "
                    "Pour importer de nouveaux stocks, vous devez supprimer cet inventaire et en créer un nouveau."
                ),
                'action_required': 'DELETE_AND_RECREATE'
            }
        else:
            # Aucun stock importé, l'import est autorisé
            return {
                'can_import': True,
                'inventory_type': 'TOURNANT',
                'existing_stocks_count': 0,
                'message': "Import autorisé pour cet inventaire de type TOURNANT.",
                'action_required': None
            }
    
    def _validate_general_inventory(self, inventory: Inventory) -> Dict[str, Any]:
        """
        Valide l'import pour un inventaire de type GENERAL.
        
        Args:
            inventory: L'inventaire à valider
            
        Returns:
            Dict[str, Any]: Résultat de la validation
        """
        # Pour les inventaires généraux, l'import est toujours autorisé
        existing_stocks_count = Stock.objects.filter(
            inventory_id=inventory.id,
            is_deleted=False
        ).count()
        
        return {
            'can_import': True,
            'inventory_type': 'GENERAL',
            'existing_stocks_count': existing_stocks_count,
            'message': f"Import autorisé pour cet inventaire de type GENERAL. {existing_stocks_count} stocks existants seront remplacés.",
            'action_required': None
        }
    
    def get_inventory_stock_info(self, inventory_id: int) -> Dict[str, Any]:
        """
        Récupère les informations sur les stocks d'un inventaire.
        
        Args:
            inventory_id: L'ID de l'inventaire
            
        Returns:
            Dict[str, Any]: Informations sur les stocks
        """
        try:
            inventory = self.inventory_repository.get_by_id(inventory_id)
            
            stocks = Stock.objects.filter(
                inventory_id=inventory_id,
                is_deleted=False
            ).select_related('product', 'location')
            
            stocks_info = []
            for stock in stocks:
                stocks_info.append({
                    'id': stock.id,
                    'product_reference': stock.product.Internal_Product_Code if stock.product else None,
                    'location_reference': stock.location.location_reference if stock.location else None,
                    'quantity': stock.quantity_available
                })
            
            return {
                'inventory_id': inventory_id,
                'inventory_type': inventory.inventory_type,
                'inventory_label': inventory.label,
                'stocks_count': len(stocks_info),
                'stocks': stocks_info
            }
            
        except InventoryNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des informations de stock: {str(e)}", exc_info=True)
            raise StockValidationError(f"Erreur lors de la récupération des informations: {str(e)}") 