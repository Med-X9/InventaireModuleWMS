from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.mobile.services.sync_service import SyncService
from apps.mobile.exceptions import UploadDataException


class UploadDataView(APIView):
    """
    API d'upload unifiée - Bonne pratique
    Traite tous les types d'uploads en une seule requête
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            sync_service = SyncService()
            
            sync_id = request.data.get('sync_id')
            if not sync_id:
                return Response({
                    'success': False,
                    'error': 'sync_id requis'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            countings = request.data.get('countings', [])
            assignments = request.data.get('assignments', [])
            
            response_data = sync_service.upload_data(sync_id, countings, assignments)
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response({
                'success': False,
                'error': f'Données invalides: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except UploadDataException as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Erreur inattendue dans UploadDataView: {str(e)}")
            return Response({
                'success': False,
                'error': 'Erreur interne du serveur'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
