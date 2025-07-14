from typing import List, Optional
from apps.users.models import UserApp
from apps.masterdata.models import Warehouse
from ..interfaces.user_interface import IUserRepository
from ..exceptions import UserNotFoundError

class UserRepository(IUserRepository):
    """
    Repository pour l'accès aux données des utilisateurs
    """
    
    def get_mobile_users(self) -> List[UserApp]:
        """
        Récupère tous les utilisateurs de type Mobile
        """
        try:
            return list(UserApp.objects.filter(type='Mobile', is_active=True).order_by('nom', 'prenom'))
        except Exception as e:
            raise UserNotFoundError(f"Erreur lors de la récupération des utilisateurs mobile: {str(e)}")

    def get_mobile_user_by_id(self, user_id: int) -> Optional[UserApp]:
        """
        Récupère un utilisateur mobile par son ID
        """
        try:
            return UserApp.objects.get(id=user_id, type='Mobile', is_active=True)
        except UserApp.DoesNotExist:
            raise UserNotFoundError(f"Utilisateur mobile avec l'ID {user_id} non trouvé")
        except Exception as e:
            raise UserNotFoundError(f"Erreur lors de la récupération de l'utilisateur mobile: {str(e)}")

    def get_mobile_users_by_warehouse(self, warehouse_id: int) -> List[UserApp]:
        """
        Récupère les utilisateurs mobile d'un warehouse spécifique
        Note: Cette méthode peut être étendue selon la logique métier
        """
        try:
            # Vérifier que le warehouse existe
            warehouse = Warehouse.objects.get(id=warehouse_id)
            
            # Pour l'instant, retourner tous les utilisateurs mobile
            # Cette logique peut être modifiée selon les besoins métier
            return list(UserApp.objects.filter(type='Mobile', is_active=True).order_by('nom', 'prenom'))
        except Warehouse.DoesNotExist:
            raise UserNotFoundError(f"Warehouse avec l'ID {warehouse_id} non trouvé")
        except Exception as e:
            raise UserNotFoundError(f"Erreur lors de la récupération des utilisateurs mobile du warehouse: {str(e)}") 