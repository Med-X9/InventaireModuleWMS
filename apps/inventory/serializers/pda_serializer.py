from rest_framework import serializers
from apps.inventory.models import Assigment

class PDASerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='session.username', read_only=True)
    
    class Meta:
        model = Assigment
        fields = ['id', 'reference', 'username']
