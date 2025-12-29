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
    """
    Vue pour récupérer les utilisateurs mobiles.

    Supporte trois modes :
    1. /mobile-users/ - Tous les utilisateurs mobiles du compte
    2. /mobile-users/inventory/{inventory_id}/ - Utilisateurs du compte de l'inventaire
    3. /mobile-users/comptage/{n_comptage}/ - Utilisateurs d'un comptage spécifique (0 = sans comptage)
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, inventory_id=None, n_comptage=None):
        """
        Récupère la liste des utilisateurs mobiles selon le contexte.

        Args:
            request: La requête HTTP
            inventory_id: ID de l'inventaire (optionnel)
            n_comptage: Numéro du comptage (optionnel) - 0 pour sans comptage

        Returns:
            Response: Liste des utilisateurs mobiles
        """
        try:
            # Récupérer l'utilisateur connecté et son compte
            user = request.user
            user_account_id = user.compte.id if hasattr(user, 'compte') and user.compte else None

            # Déterminer le mode de récupération
            if n_comptage is not None:
                # Mode filtrage par comptage
                try:
                    comptage_value = int(n_comptage) if n_comptage != '0' else None
                    result = UserService.get_mobile_users_by_comptage(comptage_value, account_id=user_account_id)
                except ValueError:
                    return Response({
                        'status': 'error',
                        'message': 'Le numéro de comptage doit être un entier',
                        'data': []
                    }, status=status.HTTP_400_BAD_REQUEST)

            elif inventory_id:
                # Mode utilisateurs du compte de l'inventaire
                result = UserService.get_mobile_users_by_inventory_account(inventory_id)

            else:
                # Mode tous les utilisateurs du compte de l'utilisateur
                if not user_account_id:
                    return Response({
                        'status': 'error',
                        'message': 'Aucun compte associé à votre utilisateur',
                        'data': []
                    }, status=status.HTTP_400_BAD_REQUEST)

                result = UserService.get_mobile_users_by_account(user_account_id)

            if result['status'] == 'error':
                return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Sérialiser et retourner
            serializer = MobileUserSerializer(result['data'], many=True)
            return Response({
                'status': 'success',
                'message': result['message'],
                'data': serializer.data
            })

        except Exception as e:
            logger.error(f"Erreur récupération utilisateurs mobiles: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Erreur inattendue lors de la récupération des utilisateurs',
                'data': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
            
