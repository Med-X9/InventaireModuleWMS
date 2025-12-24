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
    
    @staticmethod
    def get_mobile_users_by_comptage(comptage, account_id=None):
        """
        Récupère les utilisateurs mobiles filtrés par comptage et optionnellement par compte
        
        Args:
            comptage: Le numéro de comptage (1, 2, etc.) ou None pour récupérer les utilisateurs sans comptage
            account_id: L'ID du compte pour filtrer les utilisateurs (optionnel)
            
        Returns:
            dict: Dictionnaire contenant les données et un message d'information
        """
        try:
            logger.info(f"[SERVICE] Récupération des utilisateurs mobiles pour le comptage {comptage} (type: {type(comptage)}), account_id: {account_id}")
            
            # Construire le filtre de base
            filter_kwargs = {
                'type': 'Mobile',
                'is_active': True
            }
            
            # Ajouter le filtre de compte si fourni
            if account_id is not None:
                filter_kwargs['compte_id'] = account_id
            
            # Ajouter le filtre de comptage
            if comptage is None:
                filter_kwargs['comptage__isnull'] = True
                message_suffix = "sans comptage assigné"
            else:
                filter_kwargs['comptage'] = comptage
                message_suffix = f"pour le comptage {comptage}"
            
            if account_id is not None:
                message_suffix += f" du compte {account_id}"
            
            logger.info(f"[SERVICE] Filtrage: {filter_kwargs}")
            users = User.objects.filter(**filter_kwargs).order_by('nom', 'prenom')
            
            # Log pour vérifier les IDs et comptages des utilisateurs trouvés
            user_ids = list(users.values_list('id', 'comptage', 'compte_id'))
            logger.info(f"[SERVICE] IDs et comptages des utilisateurs trouvés: {user_ids}")
            
            logger.info(f"[SERVICE] Nombre d'utilisateurs trouvés: {users.count()}")
            
            if not users.exists():
                logger.info(f"Aucun utilisateur mobile trouvé {message_suffix}")
                return {
                    'status': 'success',
                    'message': f"Aucun utilisateur mobile trouvé {message_suffix}",
                    'data': []
                }
            
            logger.info(f"{users.count()} utilisateurs mobiles trouvés {message_suffix}")
            return {
                'status': 'success',
                'message': f"{users.count()} utilisateurs mobiles trouvés {message_suffix}",
                'data': users
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des utilisateurs mobiles pour le comptage {comptage}: {str(e)}")
            return {
                'status': 'error',
                'message': f"Une erreur est survenue lors de la récupération des utilisateurs mobiles: {str(e)}",
                'data': []
            }
    
    @staticmethod
    def get_mobile_users_by_account(account_id, comptage=None):
        """
        Récupère les utilisateurs mobiles filtrés par compte et optionnellement par comptage
        
        Args:
            account_id: L'ID du compte pour filtrer les utilisateurs
            comptage: Le numéro de comptage (1, 2, etc.) ou None pour récupérer tous les utilisateurs du compte
            
        Returns:
            dict: Dictionnaire contenant les données et un message d'information
        """
        try:
            logger.info(f"[SERVICE] Récupération des utilisateurs mobiles pour le compte {account_id}, comptage: {comptage}")
            
            # Construire le filtre de base
            filter_kwargs = {
                'type': 'Mobile',
                'is_active': True,
                'compte_id': account_id
            }
            
            # Ajouter le filtre de comptage si fourni
            if comptage is not None:
                filter_kwargs['comptage'] = comptage
                message_suffix = f"du compte {account_id} pour le comptage {comptage}"
            else:
                message_suffix = f"du compte {account_id}"
            
            logger.info(f"[SERVICE] Filtrage: {filter_kwargs}")
            users = User.objects.filter(**filter_kwargs).order_by('nom', 'prenom')
            
            logger.info(f"[SERVICE] Nombre d'utilisateurs trouvés: {users.count()}")
            
            if not users.exists():
                logger.info(f"Aucun utilisateur mobile trouvé {message_suffix}")
                return {
                    'status': 'success',
                    'message': f"Aucun utilisateur mobile trouvé {message_suffix}",
                    'data': []
                }
            
            logger.info(f"{users.count()} utilisateurs mobiles trouvés {message_suffix}")
            return {
                'status': 'success',
                'message': f"{users.count()} utilisateurs mobiles trouvés {message_suffix}",
                'data': users
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des utilisateurs mobiles pour le compte {account_id}: {str(e)}")
            return {
                'status': 'error',
                'message': f"Une erreur est survenue lors de la récupération des utilisateurs mobiles: {str(e)}",
                'data': []
            } 