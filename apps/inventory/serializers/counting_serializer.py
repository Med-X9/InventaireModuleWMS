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
        fields = ['order', 'count_mode', 'unit_scanned', 'entry_quantity', 'stock_situation', 'is_variant', 'n_lot', 'n_serie', 'dlc', 'show_product', 'quantity_show']

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

class CountingModeFieldsSerializer(serializers.ModelSerializer):
    champs_actifs = serializers.SerializerMethodField()

    class Meta:
        model = Counting
        fields = ['order', 'count_mode', 'champs_actifs']

    def get_champs_actifs(self, obj):
        if obj.count_mode == 'image de stock':
            return []
        mapping = {
            'unit_scanned': 'Unité scannée',
            'entry_quantity': 'Saisie quantité',
            'stock_situation': 'Situation de stock',
            'is_variant': 'Variante',
            'n_lot': 'N° lot',
            'n_serie': 'N° série',
            'dlc': 'DLC',
            'show_product': 'Afficher produit',
            'quantity_show': 'Afficher quantité',
        }
        actifs = []
        for field, label in mapping.items():
            if getattr(obj, field, False):
                actifs.append(label)
        return actifs 

class LaunchCountingRequestSerializer(serializers.Serializer):
    """Serializer pour lancer un nouveau comptage sur un job donné."""
    job_id = serializers.IntegerField(min_value=1, required=False)
    location_id = serializers.IntegerField(min_value=1, required=False)
    session_id = serializers.IntegerField(min_value=1)
    jobs = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=False
    )
    
    def validate(self, data):
        """Valide que soit (job_id, location_id) soit jobs est fourni."""
        has_old_format = data.get('job_id') and data.get('location_id')
        has_new_format = data.get('jobs')
        
        if not has_old_format and not has_new_format:
            raise serializers.ValidationError(
                "Vous devez fournir soit (job_id, location_id) soit jobs[]"
            )
        
        if has_old_format and has_new_format:
            raise serializers.ValidationError(
                "Vous ne pouvez pas fournir à la fois (job_id, location_id) et jobs[]"
            )
        
        return data