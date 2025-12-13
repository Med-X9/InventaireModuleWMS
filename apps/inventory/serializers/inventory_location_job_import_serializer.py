"""
Serializers pour l'import des InventoryLocationJob
"""
from rest_framework import serializers
from apps.masterdata.models import InventoryLocationJob


class InventoryLocationJobImportSerializer(serializers.Serializer):
    """
    Serializer pour la validation de l'import Excel
    """
    file = serializers.FileField(required=True)
    
    def validate_file(self, value):
        """
        Valide que le fichier est au format Excel
        """
        if not value.name.endswith(('.xlsx', '.xls')):
            raise serializers.ValidationError(
                "Le fichier doit être au format Excel (.xlsx ou .xls)"
            )
        return value


class InventoryLocationJobSerializer(serializers.ModelSerializer):
    """
    Serializer pour InventoryLocationJob
    """
    class Meta:
        model = InventoryLocationJob
        fields = [
            'id',
            'inventaire',
            'emplacement',
            'job',
            'session_1',
            'session_2',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

