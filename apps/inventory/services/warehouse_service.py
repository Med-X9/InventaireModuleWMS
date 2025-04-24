from apps.masterdata.models import Warehouse
from typing import List

class WarehouseService:
    @staticmethod
    def get_all_warehouses() -> List[Warehouse]:
        """
        Récupère tous les entrepôts
        """
        return Warehouse.objects.all() 