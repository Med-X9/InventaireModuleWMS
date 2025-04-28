from rest_framework.views import APIView
from rest_framework.response import Response
from apps.masterdata.models import Account
from apps.inventory.serializers.account_serializer import AccountSerializer

class AccountListView(APIView):
    """
    API View pour gérer les comptes
    """
    def get(self, request, *args, **kwargs):
        accounts = Account.objects.all()
        serializer = AccountSerializer(accounts, many=True)
        return Response(serializer.data) 