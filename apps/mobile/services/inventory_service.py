from django.utils import timezone
from apps.mobile.repositories.inventory_repository import InventoryRepository
from apps.mobile.exceptions.inventory_exceptions import (
    InventoryNotFoundException,
    AccountNotFoundException,
    DatabaseConnectionException,
    DataValidationException
)


class InventoryService:
    """Service pour la gestion des inventaires"""
    
    def __init__(self):
        self.repository = InventoryRepository()
    
    def get_inventory_users(self, inventory_id):
        """Récupère les utilisateurs du même compte qu'un inventaire"""
        try:
            # Récupérer les utilisateurs via le repository
            users = self.repository.get_users_by_inventory_account(inventory_id)
            
            # Préparer la réponse
            response_data = {
                'success': True,
                'inventory_id': inventory_id,
                'timestamp': timezone.now().isoformat(),
                'data': {
                    'users': []
                }
            }
            
            # Formater les données des utilisateurs
            for user in users:
                try:
                    user_data = self.repository.format_user_data(user)
                    response_data['data']['users'].append(user_data)
                except Exception as e:
                    print(f"Erreur lors du formatage de l'utilisateur {user.id}: {str(e)}")
                    continue
            
            # Logger la récupération
            
            return response_data
            
        except Exception as e:
            raise e 