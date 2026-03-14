from ..models import Warehouse
from ..interfaces.warehouse_interface import IWarehouseRepository
from ..exceptions import WarehouseNotFoundError

class WarehouseRepository(IWarehouseRepository):
    def get_by_id(self, warehouse_id: int):
        try:
            return Warehouse.objects.get(id=warehouse_id)
        except Warehouse.DoesNotExist:
            raise WarehouseNotFoundError(f"Entrepôt {warehouse_id} non trouvé.")

    def get_by_reference(self, reference: str):
        try:
            return Warehouse.objects.get(reference=reference)
        except Warehouse.DoesNotExist:
            raise WarehouseNotFoundError(f"Entrepôt avec la référence '{reference}' non trouvé.")

    def get_by_name(self, warehouse_name: str):
        try:
            return Warehouse.objects.get(warehouse_name=warehouse_name)
        except Warehouse.DoesNotExist:
            raise WarehouseNotFoundError(f"Entrepôt avec le nom '{warehouse_name}' non trouvé.")
        except Warehouse.MultipleObjectsReturned:
            raise WarehouseNotFoundError(f"Plusieurs entrepôts trouvés avec le nom '{warehouse_name}'. Veuillez utiliser la référence.")

    def get_all(self):
        return Warehouse.objects.all() 