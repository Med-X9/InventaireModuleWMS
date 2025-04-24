from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..services.account_service import AccountService
from ..serializers.account_serializer import AccountSerializer

class AccountListView(APIView):
    """
    Vue pour récupérer tous les comptes
    """
    def get(self, request):
        accounts = AccountService.get_all_accounts()
        serializer = AccountSerializer(accounts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK) 