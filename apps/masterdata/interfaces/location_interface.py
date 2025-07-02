from abc import ABC, abstractmethod
from typing import Any, List

class ILocationRepository(ABC):
    @abstractmethod
    def get_by_id(self, location_id: int) -> Any:
        pass

    @abstractmethod
    def get_all(self) -> List[Any]:
        pass 