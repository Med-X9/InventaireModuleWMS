"""
Interface pour le use case de gestion d'inventaire.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any

class IInventoryUseCase(ABC):
    """
    Interface pour le use case de gestion d'inventaire.
    """
    
    @abstractmethod
    def create_inventory(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un nouvel inventaire.
        
        Args:
            data: Données de l'inventaire au format JSON
            
        Returns:
            Dict[str, Any]: Résultat de la création
            
        Raises:
            InventoryValidationError: Si les données sont invalides
        """
        pass
    
    @abstractmethod
    def update_inventory(self, inventory_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour un inventaire existant.
        
        Args:
            inventory_id: ID de l'inventaire à mettre à jour
            data: Données de l'inventaire au format JSON
            
        Returns:
            Dict[str, Any]: Résultat de la mise à jour
            
        Raises:
            InventoryValidationError: Si les données sont invalides
        """
        pass
    
    @abstractmethod
    def validate_only(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valide uniquement les données sans créer l'inventaire.
        
        Args:
            data: Données de l'inventaire au format JSON
            
        Returns:
            Dict[str, Any]: Résultat de la validation
            
        Raises:
            InventoryValidationError: Si les données sont invalides
        """
        pass 