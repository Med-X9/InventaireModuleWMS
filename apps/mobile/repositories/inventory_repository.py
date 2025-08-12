from apps.inventory.models import Inventory, Setting
from apps.users.models import UserApp
from apps.mobile.exceptions.inventory_exceptions import (
    InventoryNotFoundException,
    AccountNotFoundException,
    DatabaseConnectionException,
    DataValidationException
)


class InventoryRepository:
    """Repository pour la gestion des inventaires"""
    
    def get_users_by_inventory_account(self, inventory_id):
        """Récupère les utilisateurs du même compte qu'un inventaire"""
        try:
            # Récupérer l'inventaire
            inventory = Inventory.objects.get(id=inventory_id)
            
            # Récupérer le compte via les settings de l'inventaire
            settings = inventory.awi_links.all()
            if not settings.exists():
                print(f"Aucun setting trouvé pour l'inventaire {inventory_id}")
                raise AccountNotFoundException(f"Aucun compte associé à l'inventaire {inventory_id}")
            
            # Prendre le premier setting pour récupérer le compte
            first_setting = settings.first()
            account = first_setting.account
            
            if not account:
                print(f"Aucun compte associé au setting de l'inventaire {inventory_id}")
                raise AccountNotFoundException(f"Aucun compte associé à l'inventaire {inventory_id}")
            
            # Récupérer tous les utilisateurs mobile du même compte
            users = UserApp.objects.filter(
                compte=account,
                type='Mobile',
                is_active=True
            ).order_by('nom', 'prenom')
            
            return users
            
        except Inventory.DoesNotExist:
            print(f"Inventaire avec l'ID {inventory_id} non trouvé")
            raise InventoryNotFoundException(f"Inventaire avec l'ID {inventory_id} non trouvé")
        except Exception as e:
            print(f"Erreur lors de la récupération des utilisateurs du compte d'inventaire: {str(e)}")
            raise e
    
    def format_user_data(self, user):
        """Formate les données d'un utilisateur"""
        return {
            'web_id': user.id,
            'username': user.username,
            'nom': user.nom,
            'prenom': user.prenom,
            'email': user.email,
            'type': user.type,
            'is_active': user.is_active,
            'date_joined': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None
        } 