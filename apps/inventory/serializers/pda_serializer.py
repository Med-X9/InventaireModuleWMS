from rest_framework import serializers
from apps.inventory.models import Pda

class PDASerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='session.username', read_only=True)
    
    class Meta:
        model = Pda
        fields = ['id', 'lebel','username']
