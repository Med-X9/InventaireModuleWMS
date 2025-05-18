from rest_framework import serializers
from ..models import Account

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = [
            'id',
            'account_code',
            'account_name',
            'account_statuts',
            'description'
        ] 