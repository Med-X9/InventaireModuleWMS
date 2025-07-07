from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from ..services.user_service import UserService
from ..serializers.user_serializer import MobileUserSerializer, MobileUserListSerializer
from ..exceptions import UserNotFoundError
import logging

logger = logging.getLogger(__name__)

class MobileUserListView(APIView):
    """
    API View pour lister tous les utilisateurs de type Mobile
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        """
        Récupère la liste de tous les utilisateurs de type Mobile
        
        Args:
            request: La requête HTTP
            
        Returns:
            Response: La réponse HTTP avec la liste des utilisateurs mobile
        """
        try:
            # Récupérer les utilisateurs via le service
            user_service = UserService()
            users = user_service.get_all_mobile_users()
            
            # Sérialiser les données
            serializer = MobileUserListSerializer(users, many=True)
            
            return Response({
                'status': 'success',
                'message': f"{len(serializer.data)} utilisateurs mobile trouvés",
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la récupération des utilisateurs mobile: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Une erreur inattendue est survenue lors de la récupération des utilisateurs mobile',
                'data': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class MobileUserDetailView(APIView):
    """
    API View pour récupérer un utilisateur mobile par son ID
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id, *args, **kwargs):
        """
        Récupère un utilisateur mobile par son ID
        
        Args:
            request: La requête HTTP
            user_id: L'ID de l'utilisateur
            
        Returns:
            Response: La réponse HTTP avec les détails de l'utilisateur
        """
        try:
            # Récupérer l'utilisateur via le service
            user_service = UserService()
            user = user_service.get_mobile_user_by_id(user_id)
            
            # Sérialiser les données
            serializer = MobileUserSerializer(user)
            
            return Response({
                'status': 'success',
                'message': f"Utilisateur mobile '{user.username}' trouvé avec succès",
                'data': serializer.data
            })
            
        except UserNotFoundError as e:
            logger.warning(f"Utilisateur mobile avec l'ID '{user_id}' non trouvé")
            return Response({
                'status': 'error',
                'message': str(e),
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la récupération de l'utilisateur mobile '{user_id}': {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Une erreur inattendue est survenue lors de la récupération de l\'utilisateur mobile',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class WarehouseMobileUsersView(APIView):
    """
    API View pour récupérer les utilisateurs mobile d'un warehouse spécifique
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, warehouse_id, *args, **kwargs):
        """
        Récupère les utilisateurs mobile d'un warehouse spécifique
        
        Args:
            request: La requête HTTP
            warehouse_id: L'ID du warehouse
            
        Returns:
            Response: La réponse HTTP avec la liste des utilisateurs mobile du warehouse
        """
        try:
            # Récupérer les utilisateurs via le service
            user_service = UserService()
            users = user_service.get_mobile_users_by_warehouse(warehouse_id)
            
            # Sérialiser les données
            serializer = MobileUserListSerializer(users, many=True)
            
            return Response({
                'status': 'success',
                'message': f"{len(serializer.data)} utilisateurs mobile trouvés pour le warehouse {warehouse_id}",
                'warehouse_id': warehouse_id,
                'data': serializer.data
            })
            
        except UserNotFoundError as e:
            logger.warning(f"Erreur lors de la récupération des utilisateurs mobile du warehouse '{warehouse_id}': {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e),
                'data': []
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la récupération des utilisateurs mobile du warehouse '{warehouse_id}': {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Une erreur inattendue est survenue lors de la récupération des utilisateurs mobile du warehouse',
                'data': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 