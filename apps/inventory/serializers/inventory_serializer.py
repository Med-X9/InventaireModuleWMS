"""
Serializers pour l'application inventory.
"""
from rest_framework import serializers
from ..models import Inventory, Counting, Setting
from ..services.inventory_service import InventoryService
from ..exceptions import InventoryValidationError

class CountingSerializer(serializers.ModelSerializer):
    """Serializer pour les comptages."""
    class Meta:
        model = Counting
        fields = ['order', 'count_mode', 'unit_scanned', 'entry_quantity', 'stock_situation', 'is_variant']

class InventorySerializer(serializers.ModelSerializer):
    """Serializer pour les inventaires."""
    comptages = CountingSerializer(many=True, write_only=True)
    account_id = serializers.IntegerField(write_only=True)
    warehouse_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True)
    
    class Meta:
        model = Inventory
        fields = ['id', 'label', 'date', 'account_id', 'warehouse_ids', 'comptages']
    
    def to_representation(self, instance):
        """Retourne un message de succès au lieu des données de l'inventaire."""
        return {
            "message": "L'inventaire a été créé avec succès",
            "reference": instance.reference
        }
    
    def create(self, validated_data):
        """Crée un nouvel inventaire avec ses comptages."""
        try:
            # Extraire les données de comptage
            comptages_data = validated_data.pop('comptages', [])
            
            # Renommer les champs pour correspondre à ce qu'attend le service
            validated_data['account'] = validated_data.pop('account_id')
            validated_data['warehouse'] = validated_data.pop('warehouse_ids')
            
            # Ajouter les comptages aux données validées
            validated_data['comptages'] = comptages_data
            
            inventory_service = InventoryService()
            inventory = inventory_service.create_inventory(validated_data)
            
            return inventory
            
        except InventoryValidationError as e:
            raise serializers.ValidationError(str(e))
        except Exception as e:
            raise serializers.ValidationError(f"Une erreur est survenue lors de la création de l'inventaire: {str(e)}") 