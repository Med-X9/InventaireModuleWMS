from rest_framework import serializers
from ..models import Setting

class SettingSerializer(serializers.ModelSerializer):
    """Serializer pour les paramètres."""
    account = serializers.StringRelatedField()
    warehouse = serializers.StringRelatedField()
    
    class Meta:
        model = Setting
        fields = ['id', 'account', 'warehouse'] 