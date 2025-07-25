from rest_framework import serializers
from ..models import Account

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = [
            'id',
            'reference',
            'account_name',
            'account_statuts',
            'description'
        ] 