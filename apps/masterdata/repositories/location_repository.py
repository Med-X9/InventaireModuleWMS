from ..models import Location
from ..interfaces.location_interface import ILocationRepository
from ..exceptions import LocationNotFoundError

class LocationRepository(ILocationRepository):
    def get_by_id(self, location_id: int):
        try:
            return Location.objects.get(id=location_id)
        except Location.DoesNotExist:
            raise LocationNotFoundError(f"Location {location_id} non trouvée.")

    def get_all(self):
        return Location.objects.all() 