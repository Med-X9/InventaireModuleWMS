from abc import ABC, abstractmethod
from typing import Any, List, Optional

class IUserRepository(ABC):
    @abstractmethod
    def get_mobile_users(self) -> List[Any]:
        """Récupère tous les utilisateurs de type Mobile"""
        pass

    @abstractmethod
    def get_mobile_user_by_id(self, user_id: int) -> Optional[Any]:
        """Récupère un utilisateur mobile par son ID"""
        pass

    @abstractmethod
    def get_mobile_users_by_warehouse(self, warehouse_id: int) -> List[Any]:
        """Récupère les utilisateurs mobile d'un warehouse spécifique"""
        pass

class IUserService(ABC):
    @abstractmethod
    def get_all_mobile_users(self) -> List[Any]:
        """Récupère tous les utilisateurs de type Mobile"""
        pass

    @abstractmethod
    def get_mobile_user_by_id(self, user_id: int) -> Optional[Any]:
        """Récupère un utilisateur mobile par son ID"""
        pass

    @abstractmethod
    def get_mobile_users_by_warehouse(self, warehouse_id: int) -> List[Any]:
        """Récupère les utilisateurs mobile d'un warehouse spécifique"""
        pass 