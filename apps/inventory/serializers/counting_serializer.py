from rest_framework import serializers
from ..models import Counting

class CountingCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création des comptages."""
    class Meta:
        model = Counting
        fields = [
            'order', 'count_mode', 'unit_scanned', 'entry_quantity', 
            'is_variant', 'n_lot', 'n_serie', 'dlc', 'show_product',
            'stock_situation', 'quantity_show'
        ]

class CountingDetailSerializer(serializers.ModelSerializer):
    """Serializer pour les détails des comptages."""
    class Meta:
        model = Counting
        fields = [
            'id', 'reference', 'order', 'count_mode', 
            'unit_scanned', 'entry_quantity', 'is_variant',
            'n_lot', 'n_serie', 'dlc', 'show_product',
            'stock_situation', 'quantity_show', 'inventory',
            'created_at', 'updated_at'
        ]

class CountingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Counting
        fields = ['order', 'count_mode']
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Ajouter uniquement les champs booléens qui sont True
        if instance.unit_scanned:
            data['unit_scanned'] = True
        if instance.entry_quantity:
            data['entry_quantity'] = True
        if instance.is_variant:
            data['is_variant'] = True
        if instance.stock_situation:
            data['stock_situation'] = True
        return data 