from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from apps.users.services.user_service import UserService
from ..serializers import MobileUserSerializer
import logging

logger = logging.getLogger(__name__)

class MobileUserListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, inventory_id=None):
        """
        Récupère la liste des utilisateurs mobiles
        Si inventory_id est fourni dans l'URL, récupère les utilisateurs du même compte que l'inventaire
        Sinon, récupère tous les utilisateurs mobiles
        
        Args:
            request: La requête HTTP
            inventory_id: L'ID de l'inventaire (optionnel, depuis l'URL)
            
        Returns:
            Response: La réponse HTTP avec la liste des utilisateurs mobiles
        """
        try:
            if inventory_id:
                # Récupérer les utilisateurs du même compte que l'inventaire
                result = UserService.get_mobile_users_by_inventory_account(inventory_id)
            else:
                # Récupérer tous les utilisateurs mobiles
                result = UserService.get_all_mobile_users()
            
            if result['status'] == 'error':
                return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Sérialiser les données
            serializer = MobileUserSerializer(result['data'], many=True)
            
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