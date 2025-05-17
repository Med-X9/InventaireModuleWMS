from django.db.models import Q
from ..interfaces.warehouse_interface import IWarehouseRepository
from ..models import Setting, Inventory
from ..exceptions import InventoryNotFoundError
from typing import List, Any

class WarehouseRepository(IWarehouseRepository):
    """
    Repository pour la gestion des entrepôts
    """
    
    def get_by_id(self, warehouse_id: int) -> Any:
        """
        Récupère un entrepôt par son ID
        """
        try:
            setting = Setting.objects.select_related('warehouse').get(warehouse_id=warehouse_id)
            return setting.warehouse
        except Setting.DoesNotExist:
            return None

    def get_all(self) -> List[Any]:
        """
        Récupère tous les entrepôts uniques
        """
        return Setting.objects.select_related('warehouse').values('warehouse').distinct()

    def get_by_inventory_id(self, inventory_id: int) -> List[Any]:
        """
        Récupère tous les entrepôts associés à un inventaire
        """
        try:
            inventory = Inventory.objects.get(id=inventory_id, is_deleted=False)
            return [link.warehouse for link in inventory.awi_links.all().select_related('warehouse')]
        except Inventory.DoesNotExist:
            raise InventoryNotFoundError(f"L'inventaire avec l'ID {inventory_id} n'existe pas.") 