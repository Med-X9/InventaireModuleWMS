from abc import ABC, abstractmethod
from typing import Any, List

class IZoneRepository(ABC):
    @abstractmethod
    def get_by_id(self, zone_id: int) -> Any:
        pass

    @abstractmethod
    def get_all(self) -> List[Any]:
        pass 