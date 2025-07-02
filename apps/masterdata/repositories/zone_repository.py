from ..models import Zone
from ..interfaces.zone_interface import IZoneRepository
from ..exceptions import ZoneNotFoundError

class ZoneRepository(IZoneRepository):
    def get_by_id(self, zone_id: int):
        try:
            return Zone.objects.get(id=zone_id)
        except Zone.DoesNotExist:
            raise ZoneNotFoundError(f"Zone {zone_id} non trouvée.")

    def get_all(self):
        return Zone.objects.all() 