from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..services.account_service import AccountService
from ..serializers.account_serializer import AccountSerializer
import logging

logger = logging.getLogger(__name__)

class AccountListView(APIView):
    """
    API View pour gérer les comptes
    """
    def get(self, request, *args, **kwargs):
        """
        Récupère la liste de tous les comptes
        
        Args:
            request: La requête HTTP
            
        Returns:
            Response: La réponse HTTP avec la liste des comptes
        """
        try:
            # Récupérer les comptes via le service
            accounts = AccountService.get_all_accounts()
            
            # Sérialiser les données
            serializer = AccountSerializer(accounts, many=True)
            
            return Response({
                'status': 'success',
                'message': f"{len(serializer.data)} comptes trouvés",
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la récupération des comptes: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Une erreur inattendue est survenue lors de la récupération des comptes',
                'data': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 