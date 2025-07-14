from django.contrib.auth import get_user_model
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