from ..models import Warehouse
from ..interfaces.warehouse_interface import IWarehouseRepository
from ..exceptions import WarehouseNotFoundError

class WarehouseRepository(IWarehouseRepository):
    def get_by_id(self, warehouse_id: int):
        try:
            return Warehouse.objects.get(id=warehouse_id)
        except Warehouse.DoesNotExist:
            raise WarehouseNotFoundError(f"Entrepôt {warehouse_id} non trouvé.")

    def get_all(self):
        return Warehouse.objects.all() 