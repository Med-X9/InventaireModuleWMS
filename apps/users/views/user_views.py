from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser
from apps.users.services.user_service import UserService
from ..serializers import MobileUserSerializer
import logging
import json

logger = logging.getLogger(__name__)

class MobileUserListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, inventory_id=None):
        """
        Récupère la liste des utilisateurs mobiles
        - Si un paramètre 'comptage' est fourni dans la query string, récupère les utilisateurs de ce comptage
        - Si inventory_id est fourni dans l'URL, récupère les utilisateurs du même compte que l'inventaire
        - Sinon, récupère les utilisateurs mobiles du même compte que l'utilisateur connecté
        
        Args:
            request: La requête HTTP
            inventory_id: L'ID de l'inventaire (optionnel, depuis l'URL)
            
        Query params:
            comptage: Numéro de comptage pour filtrer les utilisateurs (optionnel)
            
        Returns:
            Response: La réponse HTTP avec la liste des utilisateurs mobiles
        """
        try:
            # Récupérer l'utilisateur connecté et son compte
            user = request.user
            user_account_id = user.compte.id if hasattr(user, 'compte') and user.compte else None
            
            # Vérifier si un comptage est fourni
            # Peut être dans les query params (URL) ou dans le body (comme POST)
            comptage = None
            
            # Essayer d'abord dans les query params (URL)
            if 'comptage' in request.GET:
                comptage = request.GET.get('comptage')
            elif 'comptage' in request.query_params:
                comptage = request.query_params.get('comptage')
            
            # Sinon, essayer dans le body (comme POST) - pour les requêtes GET avec body
            # Pour GET, DRF ne parse généralement pas le body automatiquement
            # Mais si request.data existe et contient des données, l'utiliser
            if comptage is None:
                # Vérifier si request.data existe et contient des données
                if hasattr(request, 'data'):
                    # Si request.data est un dict et contient 'comptage', l'utiliser
                    if isinstance(request.data, dict) and request.data:
                        comptage = request.data.get('comptage')
                    # Si request.data est vide mais que le body existe, essayer de parser
                    elif not request.data and hasattr(request, '_body'):
                        # Utiliser _body qui est une copie du body avant lecture
                        try:
                            if request._body:
                                body_data = json.loads(request._body.decode('utf-8'))
                                if isinstance(body_data, dict):
                                    comptage = body_data.get('comptage')
                        except (json.JSONDecodeError, TypeError, ValueError, UnicodeDecodeError, AttributeError):
                            pass
            
            # Log pour déboguer
            logger.info(f"GET /mobile-users/ - comptage={comptage} (type: {type(comptage)}), inventory_id={inventory_id}, user_account_id={user_account_id}")
            logger.info(f"Query params (GET): {dict(request.GET)}")
            if hasattr(request, 'data') and request.data:
                logger.info(f"Body data: {request.data}")
            
            # Priorité 1: Si inventory_id est fourni dans l'URL
            if inventory_id:
                logger.info(f"Filtrage par inventory_id: {inventory_id}")
                result = UserService.get_mobile_users_by_inventory_account(inventory_id)
            # Priorité 2: Si comptage est fourni (dans query params ou body)
            elif comptage is not None:
                logger.info(f"Filtrage par comptage: {comptage}")
                logger.info(f"Filtrage par comptage: {comptage}")
                try:
                    # Si comptage='null' ou comptage='0', on récupère les utilisateurs sans comptage
                    if isinstance(comptage, str) and comptage.lower() in ['null', '0']:
                        comptage_value = None
                    else:
                        comptage_value = int(comptage)
                    
                    logger.info(f"Appel service avec comptage_value={comptage_value}, account_id={user_account_id}")
                    result = UserService.get_mobile_users_by_comptage(comptage_value, account_id=user_account_id)
                except (ValueError, AttributeError) as e:
                    logger.error(f"Erreur de conversion du comptage '{comptage}': {e}")
                    return Response({
                        'status': 'error',
                        'message': 'Le paramètre comptage doit être un nombre entier, "null" ou "0"',
                        'data': []
                    }, status=status.HTTP_400_BAD_REQUEST)
            # Priorité 3: Sinon, récupérer tous les utilisateurs du compte de l'utilisateur connecté
            elif user_account_id:
                logger.info(f"Récupération de tous les utilisateurs mobiles du compte {user_account_id} (aucun filtre comptage)")
                result = UserService.get_mobile_users_by_account(user_account_id)
            else:
                # Si l'utilisateur n'a pas de compte, retourner une erreur
                logger.warning("Aucun compte associé à l'utilisateur connecté")
                return Response({
                    'status': 'error',
                    'message': 'Aucun compte associé à votre utilisateur. Impossible de récupérer les utilisateurs mobiles.',
                    'data': []
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if result['status'] == 'error':
                return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Sérialiser les données
            serializer = MobileUserSerializer(result['data'], many=True)
            
            # Log pour vérifier les données sérialisées
            logger.info(f"GET - Données sérialisées: {len(serializer.data)} utilisateurs")
            if serializer.data:
                comptages_found = [u.get('comptage') for u in serializer.data]
                logger.info(f"GET - Comptages trouvés dans les données sérialisées: {comptages_found}")
            
            return Response({
                'status': 'success',
                'message': result['message'],
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la récupération des utilisateurs mobiles: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Une erreur inattendue est survenue lors de la récupération des utilisateurs mobiles',
                'data': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """
        Récupère la liste des utilisateurs mobiles filtrés par comptage
        Le comptage est fourni dans le body de la requête
        
        Args:
            request: La requête HTTP
            
        Body params:
            comptage: Numéro de comptage pour filtrer les utilisateurs (requis)
                     Peut être un entier (1, 2, 3...) ou null/0 pour les utilisateurs sans comptage
            
        Returns:
            Response: La réponse HTTP avec la liste des utilisateurs mobiles filtrés par comptage
            
        Example:
            POST /api/users/mobile-users/
            {
                "comptage": 1
            }
        """
        try:
            # Récupérer le comptage depuis le body
            comptage = request.data.get('comptage', None)
            
            # Log pour déboguer
            logger.info(f"POST /mobile-users/ appelé avec comptage: {comptage} (type: {type(comptage)})")
            logger.info(f"Body complet reçu: {request.data}")
            
            if comptage is None:
                logger.warning("Paramètre comptage manquant dans le body")
                return Response({
                    'status': 'error',
                    'message': 'Le paramètre comptage est requis dans le body',
                    'data': []
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Gérer le cas où comptage est 0 ou 'null' pour récupérer les utilisateurs sans comptage
            try:
                if isinstance(comptage, str) and comptage.lower() in ['null', '0']:
                    comptage_value = None
                elif comptage == 0 or comptage == '0':
                    comptage_value = None
                else:
                    comptage_value = int(comptage)
                
                logger.info(f"Valeur de comptage après traitement: {comptage_value}")
            except (ValueError, TypeError) as e:
                logger.error(f"Erreur de conversion du comptage: {e}")
                return Response({
                    'status': 'error',
                    'message': 'Le paramètre comptage doit être un nombre entier, 0 ou "null"',
                    'data': []
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Récupérer l'utilisateur connecté et son compte
            user = request.user
            user_account_id = user.compte.id if hasattr(user, 'compte') and user.compte else None
            
            # Appeler le service pour récupérer les utilisateurs
            logger.info(f"Appel de get_mobile_users_by_comptage avec comptage_value={comptage_value}, account_id={user_account_id}")
            result = UserService.get_mobile_users_by_comptage(comptage_value, account_id=user_account_id)
            
            if result['status'] == 'error':
                return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Sérialiser les données
            serializer = MobileUserSerializer(result['data'], many=True)
            
            # Log pour vérifier les données sérialisées
            logger.info(f"POST - Données sérialisées: {len(serializer.data)} utilisateurs")
            if serializer.data:
                comptages_found = [u.get('comptage') for u in serializer.data]
                logger.info(f"POST - Comptages trouvés dans les données sérialisées: {comptages_found}")
            
            return Response({
                'status': 'success',
                'message': result['message'],
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la récupération des utilisateurs mobiles par comptage: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Une erreur inattendue est survenue lors de la récupération des utilisateurs mobiles',
                'data': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 