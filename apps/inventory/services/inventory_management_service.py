"""
Service de gestion d'inventaire pour la création et la mise à jour.
"""
from typing import Dict, Any
from ..interfaces.inventory_interface import IInventoryUpdateService
from ..usecases.inventory_management import InventoryManagementUseCase
from ..exceptions import InventoryValidationError, InventoryNotFoundError
from ..models import Inventory
import logging

logger = logging.getLogger(__name__)

class InventoryManagementService(IInventoryUpdateService):
    """
    Service de gestion d'inventaire qui utilise le use case générique.
    
    Ce service implémente l'interface IInventoryUpdateService et utilise
    le InventoryManagementUseCase pour gérer à la fois la création et la mise à jour.
    """
    
    def __init__(self, use_case: InventoryManagementUseCase = None):
        self.use_case = use_case or InventoryManagementUseCase()
    
    def create_inventory(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un nouvel inventaire en utilisant le use case.
        
        Args:
            data: Les données de l'inventaire
            
        Returns:
            Dict[str, Any]: Résultat de la création
            
        Raises:
            InventoryValidationError: Si les données sont invalides
        """
        try:
            return self.use_case.create(data)
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'inventaire: {str(e)}", exc_info=True)
            raise InventoryValidationError(f"Erreur lors de la création de l'inventaire: {str(e)}")
    
    def update_inventory(self, inventory_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour un inventaire avec validation complète en utilisant le use case.
        
        Args:
            inventory_id: L'ID de l'inventaire à mettre à jour
            data: Les nouvelles données de l'inventaire
            
        Returns:
            Dict[str, Any]: Résultat de la mise à jour
            
        Raises:
            InventoryNotFoundError: Si l'inventaire n'existe pas
            InventoryValidationError: Si les données sont invalides
        """
        try:
            return self.use_case.update(inventory_id, data)
            
        except InventoryNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de l'inventaire: {str(e)}", exc_info=True)
            raise InventoryValidationError(f"Erreur lors de la mise à jour de l'inventaire: {str(e)}")
    
    def validate_update_data(self, data: Dict[str, Any]) -> None:
        """
        Valide les données de mise à jour en utilisant le use case.
        
        Args:
            data: Les données à valider
            
        Raises:
            InventoryValidationError: Si les données sont invalides
        """
        try:
            self.use_case.validate_only(data)
        except Exception as e:
            logger.error(f"Erreur de validation des données: {str(e)}", exc_info=True)
            raise InventoryValidationError(f"Erreur de validation des données: {str(e)}")
    
    def validate_create_data(self, data: Dict[str, Any]) -> None:
        """
        Valide les données de création en utilisant le use case.
        
        Args:
            data: Les données à valider
            
        Raises:
            InventoryValidationError: Si les données sont invalides
        """
        try:
            self.use_case.validate_only(data)
        except Exception as e:
            logger.error(f"Erreur de validation des données: {str(e)}", exc_info=True)
            raise InventoryValidationError(f"Erreur de validation des données: {str(e)}") 