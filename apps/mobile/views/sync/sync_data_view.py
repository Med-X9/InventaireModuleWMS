from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.mobile.services.sync_service import SyncService
from apps.mobile.exceptions import (
    UserNotFoundException,
    AccountNotFoundException,
    SyncDataException
)


class SyncDataView(APIView):
    """
    API de synchronisation intelligente - Bonne pratique
    Récupère toutes les données nécessaires en une seule requête
    Si user_id est fourni dans l'URL, récupère les inventaires du même compte que cet utilisateur
    Sinon, récupère tous les inventaires en réalisation
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id=None):
        try:
            sync_service = SyncService()
            
            # Récupérer les paramètres de synchronisation
            inventory_id = request.GET.get('inventory_id')
            
            # Si user_id est fourni dans l'URL, utiliser cet utilisateur
            # Sinon, utiliser l'utilisateur connecté
            if user_id:
                target_user_id = user_id
            else:
                target_user_id = request.user.id
            
            response_data = sync_service.sync_data(target_user_id, inventory_id)
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except (UserNotFoundException, AccountNotFoundException) as e:
            return Response({
                'success': False,
                'error': str(e),
                'error_type': 'NOT_FOUND'
            }, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({
                'success': False,
                'error': f'Paramètre invalide: {str(e)}',
                'error_type': 'INVALID_PARAMETER'
            }, status=status.HTTP_400_BAD_REQUEST)
        except SyncDataException as e:
            return Response({
                'success': False,
                'error': str(e),
                'error_type': 'SYNC_ERROR'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Erreur inattendue dans SyncDataView: {str(e)}")
            return Response({
                'success': False,
                'error': 'Erreur interne du serveur',
                'error_type': 'INTERNAL_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
