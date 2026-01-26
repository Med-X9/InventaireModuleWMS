"""
Repository pour la gestion des Settings (liens entre Account, Warehouse et Inventory).
"""
from typing import List, Dict, Any, Optional
from ..models import Setting, Inventory
from ..exceptions.inventory_exceptions import InventoryNotFoundError


class SettingRepository:
    """
    Repository pour la gestion des Settings.
    """
    
    def get_by_id(self, setting_id: int) -> Setting:
        """
        Récupère un Setting par son ID.
        
        Args:
            setting_id: L'ID du Setting
            
        Returns:
            Setting: Le Setting trouvé
            
        Raises:
            InventoryNotFoundError: Si le Setting n'existe pas
        """
        try:
            return Setting.objects.get(id=setting_id, is_deleted=False)
        except Setting.DoesNotExist:
            raise InventoryNotFoundError(f"Le Setting avec l'ID {setting_id} n'existe pas.")
    
    def get_by_inventory_id(self, inventory_id: int) -> List[Setting]:
        """
        Récupère tous les Settings associés à un inventaire.
        
        Args:
            inventory_id: L'ID de l'inventaire
            
        Returns:
            List[Setting]: Liste des Settings
        """
        return Setting.objects.filter(
            inventory_id=inventory_id,
            is_deleted=False
        ).select_related('warehouse', 'account', 'inventory')
    
    def get_by_warehouse_and_inventory(self, warehouse_id: int, inventory_id: int) -> Setting:
        """
        Récupère un Setting par warehouse et inventaire.
        
        Args:
            warehouse_id: L'ID du warehouse
            inventory_id: L'ID de l'inventaire
            
        Returns:
            Setting: Le Setting trouvé
            
        Raises:
            InventoryNotFoundError: Si le Setting n'existe pas
        """
        try:
            return Setting.objects.get(
                warehouse_id=warehouse_id,
                inventory_id=inventory_id,
                is_deleted=False
            )
        except Setting.DoesNotExist:
            raise InventoryNotFoundError(
                f"Le Setting pour l'inventaire {inventory_id} et le warehouse {warehouse_id} n'existe pas."
            )
    
    def get_lancees_by_inventory(self, inventory_id: int) -> List[Setting]:
        """
        Récupère tous les Settings avec le statut 'LANCEE' pour un inventaire.
        
        Args:
            inventory_id: L'ID de l'inventaire
            
        Returns:
            List[Setting]: Liste des Settings lancés
        """
        return Setting.objects.filter(
            inventory_id=inventory_id,
            status='LANCEE',
            is_deleted=False
        )
    
    def update_status(self, setting_id: int, new_status: str) -> Setting:
        """
        Met à jour le statut d'un Setting.
        
        Args:
            setting_id: L'ID du Setting
            new_status: Le nouveau statut
            
        Returns:
            Setting: Le Setting mis à jour
        """
        setting = self.get_by_id(setting_id)
        setting.status = new_status
        setting.save()
        return setting
    
    def has_inventory_in_realisation(self, inventory_id: int) -> bool:
        """
        Vérifie si un inventaire est en statut 'EN REALISATION'.
        
        Args:
            inventory_id: L'ID de l'inventaire
            
        Returns:
            bool: True si l'inventaire est en réalisation, False sinon
        """
        try:
            inventory = Inventory.objects.get(id=inventory_id, is_deleted=False)
            return inventory.status == 'EN REALISATION'
        except Inventory.DoesNotExist:
            return False

