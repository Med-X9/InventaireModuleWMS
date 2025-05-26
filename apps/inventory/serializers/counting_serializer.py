from rest_framework import serializers
from ..models import Counting

class CountingCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création des comptages."""
    class Meta:
        model = Counting
        fields = ['order', 'count_mode', 'unit_scanned', 'entry_quantity', 'stock_situation', 'is_variant']

class CountingDetailSerializer(serializers.ModelSerializer):
    """Serializer pour les détails des comptages."""
    class Meta:
        model = Counting
        fields = ['order', 'count_mode', 'unit_scanned', 'entry_quantity', 'stock_situation', 'is_variant','status']

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