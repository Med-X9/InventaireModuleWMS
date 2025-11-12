from django.db.models import Q
from ..interfaces.warehouse_interface import IWarehouseRepository
from ..models import Setting, Inventory
from apps.masterdata.models import Warehouse, Location
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

    def get_by_account_id(self, account_id: int) -> List[Warehouse]:
        """
        Récupère tous les entrepôts associés à un compte donné.
        """
        locations = (
            Location.objects.select_related('sous_zone__zone__warehouse', 'regroupement')
            .filter(regroupement__account_id=account_id, sous_zone__zone__warehouse__isnull=False)
            .order_by('sous_zone__zone__warehouse_id')
        )

        warehouses: List[Warehouse] = []
        seen_ids = set()

        for location in locations:
            warehouse = location.sous_zone.zone.warehouse
            if warehouse.id not in seen_ids:
                seen_ids.add(warehouse.id)
                warehouses.append(warehouse)

        return warehouses