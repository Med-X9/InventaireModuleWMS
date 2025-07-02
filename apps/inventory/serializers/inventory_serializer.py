"""
Serializers pour l'application inventory.
"""
from rest_framework import serializers
from ..models import Inventory, Counting, Setting, Assigment
from ..services.inventory_service import InventoryService
from ..exceptions import InventoryValidationError
from apps.masterdata.models import Account, Warehouse
from .counting_serializer import CountingCreateSerializer, CountingDetailSerializer, CountingSerializer, CountingModeFieldsSerializer
from apps.users.serializers import UserAppSerializer

class InventoryCreateSerializer(serializers.Serializer):
    label = serializers.CharField()
    date = serializers.DateField()
    account_id = serializers.IntegerField()
    inventory_type = serializers.ChoiceField(choices=[('TOURNANT', 'TOURNANT'), ('GENERAL', 'GENERAL')], default='GENERAL')
    warehouse = serializers.ListField(
        child=serializers.DictField(),
        required=True
    )
    comptages = serializers.ListField(
        child=serializers.DictField(),
        required=True
    )

    def validate(self, data):
        """
        Valide les données de l'inventaire selon les règles métier.
        """
        errors = []
        
        # Validation des entrepôts
        for i, warehouse_info in enumerate(data['warehouse']):
            if not warehouse_info.get('id'):
                raise serializers.ValidationError(f"L'entrepôt {i+1} doit avoir un ID")
        
        # Validation des comptages
        comptages = data.get('comptages', [])
        
        # Vérifier qu'il y a exactement 3 comptages
        if len(comptages) != 3:
            raise serializers.ValidationError("Un inventaire doit contenir exactement 3 comptages")
        
        # Trier les comptages par ordre
        comptages_sorted = sorted(comptages, key=lambda x: x.get('order', 0))
        
        # Vérifier que les ordres sont 1, 2, 3
        orders = [c.get('order') for c in comptages_sorted]
        if orders != [1, 2, 3]:
            raise serializers.ValidationError("Les comptages doivent avoir les ordres 1, 2, 3")
        
        # Validation des champs obligatoires pour chaque comptage
        for i, comptage in enumerate(comptages_sorted, 1):
            if not comptage.get('order'):
                raise serializers.ValidationError(f"Le comptage {i} doit avoir un ordre")
            if not comptage.get('count_mode'):
                raise serializers.ValidationError(f"Le comptage {i} doit avoir un mode de comptage")
        
        # Récupérer les modes de comptage par ordre
        count_modes = [c.get('count_mode') for c in comptages_sorted]
        
        # Vérifier que tous les modes sont valides
        valid_modes = ['en vrac', 'par article', 'image de stock']
        for i, mode in enumerate(count_modes):
            if mode not in valid_modes:
                raise serializers.ValidationError(f"Comptage {i+1}: Mode de comptage invalide '{mode}'")
        
        # Validation des combinaisons autorisées
        first_mode = count_modes[0]
        second_mode = count_modes[1]
        third_mode = count_modes[2]
        
        # Scénario 1: Premier comptage = "image de stock"
        if first_mode == "image de stock":
            # Les 2e et 3e comptages doivent être du même mode (soit "en vrac", soit "par article")
            if second_mode != third_mode:
                raise serializers.ValidationError("Si le premier comptage est 'image de stock', les 2e et 3e comptages doivent avoir le même mode")
            
            if second_mode not in ["en vrac", "par article"]:
                raise serializers.ValidationError("Si le premier comptage est 'image de stock', les 2e et 3e comptages doivent être 'en vrac' ou 'par article'")
        
        # Scénario 2: Premier comptage = "en vrac" ou "par article"
        elif first_mode in ["en vrac", "par article"]:
            # Tous les comptages doivent être "en vrac" ou "par article"
            for i, mode in enumerate(count_modes):
                if mode not in ["en vrac", "par article"]:
                    raise serializers.ValidationError(f"Si le premier comptage n'est pas 'image de stock', tous les comptages doivent être 'en vrac' ou 'par article' (comptage {i+1}: '{mode}')")
        
        return data

class InventoryGetByIdSerializer(serializers.ModelSerializer):
    """Serializer pour récupérer un inventaire par son ID avec le format spécifique."""
    account_id = serializers.SerializerMethodField()
    warehouse_ids = serializers.SerializerMethodField()
    comptages = serializers.SerializerMethodField()

    class Meta:
        model = Inventory
        fields = ['label', 'date', 'account_id', 'warehouse_ids', 'comptages']

    def get_account_id(self, obj):
        setting = Setting.objects.filter(inventory=obj).first()
        return setting.account.id if setting else None

    def get_warehouse_ids(self, obj):
        settings = Setting.objects.filter(inventory=obj)
        return [setting.warehouse.id for setting in settings]

    def get_comptages(self, obj):
        countings = Counting.objects.filter(inventory=obj).order_by('order')
        return CountingDetailSerializer(countings, many=True).data

class PdaTeamSerializer(serializers.ModelSerializer):
    """Serializer pour les membres de l'équipe PDA"""
    user = UserAppSerializer(source='session', read_only=True)

    class Meta:
        model = Assigment
        fields = ['id', 'reference', 'user']

class InventoryDetailSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les détails d'un inventaire.
    """
    account_name = serializers.SerializerMethodField()
    warehouse_name = serializers.SerializerMethodField()
    comptages = serializers.SerializerMethodField()
    equipe = serializers.SerializerMethodField()

    class Meta:
        model = Inventory
        fields = [
            'id', 'label', 'date', 'status', 'inventory_type',
            'en_preparation_status_date',
            'en_realisation_status_date', 'termine_status_date',
            'cloture_status_date', 'account_name', 'warehouse_name',
            'comptages', 'equipe'
        ]

    def get_account_name(self, obj):
        setting = Setting.objects.filter(inventory=obj).first()
        return setting.account.account_name if setting else None

    def get_warehouse_name(self, obj):
        settings = Setting.objects.filter(inventory=obj)
        return [setting.warehouse.warehouse_name for setting in settings]

    def get_comptages(self, obj):
        countings = Counting.objects.filter(inventory=obj).order_by('order')
        return CountingDetailSerializer(countings, many=True).data

    def get_equipe(self, obj):
        pdas = Assigment.objects.filter(job__inventory=obj)
        return PdaTeamSerializer(pdas, many=True).data

class InventorySerializer(serializers.ModelSerializer):
    account_name = serializers.SerializerMethodField()
    warehouse_name = serializers.SerializerMethodField()
    comptages = serializers.SerializerMethodField()
    equipe = serializers.SerializerMethodField()

    class Meta:
        model = Inventory
        fields = [
            'id', 'label', 'date', 'status', 'inventory_type',
            'en_preparation_status_date', 'en_realisation_status_date',
            'termine_status_date', 'cloture_status_date',
            'account_name', 'warehouse_name', 'comptages', 'equipe'
        ]

    def get_account_name(self, obj):
        setting = Setting.objects.filter(inventory=obj).first()
        return setting.account.account_name if setting else None

    def get_warehouse_name(self, obj):
        settings = Setting.objects.filter(inventory=obj)
        return [setting.warehouse.warehouse_name for setting in settings]

    def get_comptages(self, obj):
        countings = Counting.objects.filter(inventory=obj).order_by('order')
        return CountingSerializer(countings, many=True).data

    def get_equipe(self, obj):
        pdas = Assigment.objects.filter(job__inventory=obj)
        return PdaTeamSerializer(pdas, many=True).data

class InventoryTeamSerializer(serializers.ModelSerializer):
    """Serializer pour récupérer l'équipe d'un inventaire"""
    user = UserAppSerializer(source='session', read_only=True)

    class Meta:
        model = Assigment
        fields = ['id', 'reference', 'user']

class InventoryWarehouseStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques des warehouses d'un inventaire"""
    warehouse_id = serializers.IntegerField()
    warehouse_reference = serializers.CharField()
    warehouse_name = serializers.CharField()
    jobs_count = serializers.IntegerField()
    teams_count = serializers.IntegerField()
    
    class Meta:
        fields = ['warehouse_id', 'warehouse_reference', 'warehouse_name', 'jobs_count', 'teams_count'] 

class InventoryUpdateSerializer(serializers.Serializer):
    """Serializer pour la mise à jour d'inventaire."""
    label = serializers.CharField(required=False)
    date = serializers.DateField(required=False)
    account_id = serializers.IntegerField(required=False)
    inventory_type = serializers.ChoiceField(
        choices=[('TOURNANT', 'TOURNANT'), ('GENERAL', 'GENERAL')], 
        required=False
    )
    warehouse = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )
    comptages = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )

    def validate(self, data):
        """
        Valide les données de mise à jour selon les règles métier.
        """
        errors = []
        
        # Validation des entrepôts si fournis
        warehouse = data.get('warehouse', [])
        if warehouse:
            for i, warehouse_info in enumerate(warehouse):
                if not warehouse_info.get('id'):
                    raise serializers.ValidationError(f"L'entrepôt {i+1} doit avoir un ID")
        
        # Validation des comptages si fournis
        comptages = data.get('comptages', [])
        if comptages:
            # Vérifier qu'il y a exactement 3 comptages
            if len(comptages) != 3:
                raise serializers.ValidationError("Un inventaire doit contenir exactement 3 comptages")
            
            # Trier les comptages par ordre
            comptages_sorted = sorted(comptages, key=lambda x: x.get('order', 0))
            
            # Vérifier que les ordres sont 1, 2, 3
            orders = [c.get('order') for c in comptages_sorted]
            if orders != [1, 2, 3]:
                raise serializers.ValidationError("Les comptages doivent avoir les ordres 1, 2, 3")
            
            # Validation des champs obligatoires pour chaque comptage
            for i, comptage in enumerate(comptages_sorted, 1):
                if not comptage.get('order'):
                    raise serializers.ValidationError(f"Le comptage {i} doit avoir un ordre")
                if not comptage.get('count_mode'):
                    raise serializers.ValidationError(f"Le comptage {i} doit avoir un mode de comptage")
            
            # Récupérer les modes de comptage par ordre
            count_modes = [c.get('count_mode') for c in comptages_sorted]
            
            # Vérifier que tous les modes sont valides
            valid_modes = ['en vrac', 'par article', 'image de stock']
            for i, mode in enumerate(count_modes):
                if mode not in valid_modes:
                    raise serializers.ValidationError(f"Comptage {i+1}: Mode de comptage invalide '{mode}'")
            
            # Validation des combinaisons autorisées
            first_mode = count_modes[0]
            second_mode = count_modes[1]
            third_mode = count_modes[2]
            
            # Scénario 1: Premier comptage = "image de stock"
            if first_mode == "image de stock":
                # Les 2e et 3e comptages doivent être du même mode (soit "en vrac", soit "par article")
                if second_mode != third_mode:
                    raise serializers.ValidationError("Si le premier comptage est 'image de stock', les 2e et 3e comptages doivent avoir le même mode")
                
                if second_mode not in ["en vrac", "par article"]:
                    raise serializers.ValidationError("Si le premier comptage est 'image de stock', les 2e et 3e comptages doivent être 'en vrac' ou 'par article'")
            
            # Scénario 2: Premier comptage = "en vrac" ou "par article"
            elif first_mode in ["en vrac", "par article"]:
                # Tous les comptages doivent être "en vrac" ou "par article"
                for i, mode in enumerate(count_modes):
                    if mode not in ["en vrac", "par article"]:
                        raise serializers.ValidationError(f"Si le premier comptage n'est pas 'image de stock', tous les comptages doivent être 'en vrac' ou 'par article' (comptage {i+1}: '{mode}')")
        
        return data 

class InventoryDetailModeFieldsSerializer(serializers.ModelSerializer):
    account_name = serializers.SerializerMethodField()
    warehouse_name = serializers.SerializerMethodField()
    comptages = serializers.SerializerMethodField()
    equipe = serializers.SerializerMethodField()
    class Meta:
        model = Inventory
        fields = [
            'id', 'label', 'date', 'status', 'inventory_type',
            'en_preparation_status_date',
            'en_realisation_status_date', 'termine_status_date',
            'cloture_status_date', 'account_name', 'warehouse_name',
            'comptages', 'equipe'
        ]
    def get_account_name(self, obj):
        setting = Setting.objects.filter(inventory=obj).first()
        return setting.account.account_name if setting else None
    def get_warehouse_name(self, obj):
        settings = Setting.objects.filter(inventory=obj)
        return [setting.warehouse.warehouse_name for setting in settings]
    def get_comptages(self, obj):
        countings = Counting.objects.filter(inventory=obj).order_by('order')
        return CountingModeFieldsSerializer(countings, many=True).data
    def get_equipe(self, obj):
        pdas = Assigment.objects.filter(job__inventory=obj)
        return PdaTeamSerializer(pdas, many=True).data 
