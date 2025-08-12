from django.contrib.auth import get_user_model
from apps.inventory.models import Inventory
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class UserService:
    @staticmethod
    def get_all_mobile_users():
        """
        Récupère tous les utilisateurs de type mobile
        
        Returns:
            dict: Dictionnaire contenant les données et un message d'information
        """
        try:
            logger.info("Récupération de tous les utilisateurs mobiles")
            
            # Récupérer tous les utilisateurs de type mobile
            users = User.objects.filter(type='Mobile')
            
            if not users.exists():
                logger.info("Aucun utilisateur mobile trouvé")
                return {
                    'status': 'success',
                    'message': 'Aucun utilisateur mobile trouvé',
                    'data': []
                }
            
            logger.info(f"{users.count()} utilisateurs mobiles trouvés")
            return {
                'status': 'success',
                'message': f"{users.count()} utilisateurs mobiles trouvés",
                'data': users
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des utilisateurs mobiles: {str(e)}")
            return {
                'status': 'error',
                'message': f"Une erreur est survenue lors de la récupération des utilisateurs mobiles: {str(e)}",
                'data': []
            }
    
    @staticmethod
    def get_mobile_users_by_inventory_account(inventory_id):
        """
        Récupère les utilisateurs mobiles du même compte qu'un inventaire
        
        Args:
            inventory_id: L'ID de l'inventaire
            
        Returns:
            dict: Dictionnaire contenant les données et un message d'information
        """
        try:
            logger.info(f"Récupération des utilisateurs mobiles pour l'inventaire {inventory_id}")
            
            # Récupérer l'inventaire
            try:
                inventory = Inventory.objects.get(id=inventory_id)
            except Inventory.DoesNotExist:
                logger.warning(f"Inventaire avec l'ID {inventory_id} non trouvé")
                return {
                    'status': 'error',
                    'message': f"Inventaire avec l'ID {inventory_id} non trouvé",
                    'data': []
                }
            
            # Récupérer le compte via les settings de l'inventaire
            settings = inventory.awi_links.all()
            if not settings.exists():
                logger.warning(f"Aucun compte associé à l'inventaire {inventory_id}")
                return {
                    'status': 'success',
                    'message': 'Aucun compte associé à cet inventaire',
                    'data': []
                }
            
            # Prendre le premier setting pour récupérer le compte
            first_setting = settings.first()
            account = first_setting.account
            
            # Récupérer tous les utilisateurs mobile du même compte
            users = User.objects.filter(
                compte=account,
                type='Mobile',
                is_active=True
            ).order_by('nom', 'prenom')
            
            if not users.exists():
                logger.info(f"Aucun utilisateur mobile trouvé pour le compte de l'inventaire {inventory_id}")
                return {
                    'status': 'success',
                    'message': f"Aucun utilisateur mobile trouvé pour le compte de l'inventaire {inventory_id}",
                    'data': []
                }
            
            logger.info(f"{users.count()} utilisateurs mobiles trouvés pour l'inventaire {inventory_id}")
            return {
                'status': 'success',
                'message': f"{users.count()} utilisateurs mobiles trouvés pour le compte de l'inventaire {inventory_id}",
                'data': users
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des utilisateurs mobiles pour l'inventaire {inventory_id}: {str(e)}")
            return {
                'status': 'error',
                'message': f"Une erreur est survenue lors de la récupération des utilisateurs mobiles: {str(e)}",
                'data': []
            } 