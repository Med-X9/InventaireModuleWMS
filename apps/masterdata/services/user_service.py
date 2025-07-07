from typing import List, Optional
import logging
from apps.users.models import UserApp
from ..repositories.user_repository import UserRepository
from ..interfaces.user_interface import IUserService
from ..exceptions import UserNotFoundError

logger = logging.getLogger(__name__)

class UserService(IUserService):
    """
    Service pour les opérations de gestion des utilisateurs
    """
    
    def __init__(self):
        self.repository = UserRepository()

    def get_all_mobile_users(self) -> List[UserApp]:
        """
        Récupère tous les utilisateurs de type Mobile
        """
        try:
            logger.info("Récupération de tous les utilisateurs mobile")
            users = self.repository.get_mobile_users()
            logger.info(f"{len(users)} utilisateurs mobile trouvés")
            return users
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des utilisateurs mobile: {str(e)}")
            raise

    def get_mobile_user_by_id(self, user_id: int) -> Optional[UserApp]:
        """
        Récupère un utilisateur mobile par son ID
        """
        try:
            logger.info(f"Récupération de l'utilisateur mobile avec l'ID: {user_id}")
            user = self.repository.get_mobile_user_by_id(user_id)
            logger.info(f"Utilisateur mobile trouvé: {user.username}")
            return user
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'utilisateur mobile '{user_id}': {str(e)}")
            raise

    def get_mobile_users_by_warehouse(self, warehouse_id: int) -> List[UserApp]:
        """
        Récupère les utilisateurs mobile d'un warehouse spécifique
        """
        try:
            logger.info(f"Récupération des utilisateurs mobile pour le warehouse: {warehouse_id}")
            users = self.repository.get_mobile_users_by_warehouse(warehouse_id)
            logger.info(f"{len(users)} utilisateurs mobile trouvés pour le warehouse {warehouse_id}")
            return users
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des utilisateurs mobile du warehouse '{warehouse_id}': {str(e)}")
            raise 