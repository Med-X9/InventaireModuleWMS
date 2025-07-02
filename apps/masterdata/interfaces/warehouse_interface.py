from abc import ABC, abstractmethod
from typing import Any, List

class IWarehouseRepository(ABC):
    @abstractmethod
    def get_by_id(self, warehouse_id: int) -> Any:
        pass

    @abstractmethod
    def get_all(self) -> List[Any]:
        pass 