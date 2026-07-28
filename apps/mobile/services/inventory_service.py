from django.utils import timezone
from apps.mobile.repositories.inventory_repository import InventoryRepository
from apps.mobile.repositories.sync_repository import SyncRepository


class InventoryService:
    """Service pour la gestion des inventaires"""
    
    def __init__(self):
        self.repository = InventoryRepository()
        self.sync_repository = SyncRepository()
    
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
    
    def get_user_inventories(self, user_id):
        """
        Inventaires EN REALISATION de l'utilisateur connecté,
        avec uniquement les magasins où il est affecté.

        Args:
            user_id: ID de l'utilisateur authentifié (session)

        Returns:
            Dict avec liste inventaires + warehouses filtrés par affectation
        """
        try:
            inventories = self.sync_repository.get_inventories_by_user_assignments(user_id)

            inventories_list = []
            for inventory in inventories:
                try:
                    # Uniquement les magasins liés aux jobs de cette session
                    warehouses = self.sync_repository.get_warehouses_for_user_inventory(
                        user_id, inventory.id
                    )

                    warehouses_list = [
                        {
                            'web_id': warehouse.id,
                            'reference': warehouse.reference,
                            'warehouse_name': warehouse.warehouse_name,
                            'warehouse_type': warehouse.warehouse_type,
                            'status': warehouse.status,
                            'description': warehouse.description,
                            'address': warehouse.address,
                        }
                        for warehouse in warehouses
                    ]

                    # Pas d'inventaire sans magasin concerné pour cet utilisateur
                    if not warehouses_list:
                        continue

                    inventories_list.append({
                        'web_id': inventory.id,
                        'reference': inventory.reference,
                        'label': inventory.label,
                        'status': inventory.status,
                        'inventory_type': inventory.inventory_type,
                        'date': inventory.date.isoformat() if inventory.date else None,
                        'en_realisation_status_date': (
                            inventory.en_realisation_status_date.isoformat()
                            if inventory.en_realisation_status_date
                            else None
                        ),
                        'created_at': (
                            inventory.created_at.isoformat() if inventory.created_at else None
                        ),
                        'updated_at': (
                            inventory.updated_at.isoformat() if inventory.updated_at else None
                        ),
                        'warehouses': warehouses_list,
                    })
                except Exception as e:
                    print(f"Erreur lors du formatage de l'inventaire {inventory.id}: {str(e)}")
                    continue

            return {'inventories': inventories_list}

        except Exception as e:
            raise e
 