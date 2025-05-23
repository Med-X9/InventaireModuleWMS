"""
Serializers pour l'application inventory.
"""
from rest_framework import serializers
from ..models import Inventory, Counting, Setting
from ..services.inventory_service import InventoryService
from ..exceptions import InventoryValidationError
from apps.masterdata.models import Account, Warehouse
from .counting_serializer import CountingCreateSerializer, CountingDetailSerializer, CountingSerializer

class InventoryCreateSerializer(serializers.Serializer):
    label = serializers.CharField()
    date = serializers.DateField()
    account_id = serializers.IntegerField(source='account')
    warehouse_ids = serializers.ListField(
        child=serializers.IntegerField(),
        source='warehouse'
    )
    comptages = serializers.ListField(
        child=serializers.DictField(),
        required=True
    )

    def validate(self, data):
        """
        Valide les données de l'inventaire.
        """
        # Convertir les noms de champs pour correspondre à ce que le service attend
        validated_data = {
            'label': data['label'],
            'date': data['date'],
            'account': data['account'],
            'warehouse': data['warehouse'],
            'comptages': data['comptages']
        }
        return validated_data

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

class InventoryDetailSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les détails d'un inventaire.
    """
    account_name = serializers.SerializerMethodField()
    warehouse_name = serializers.SerializerMethodField()
    comptages = serializers.SerializerMethodField()

    class Meta:
        model = Inventory
        fields = [
            'id', 'label', 'date', 'status', 'end_status_date',
            'lunch_status_date', 'current_status_date', 'pending_status_date',
            'account_name', 'warehouse_name', 'comptages'
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

class InventorySerializer(serializers.ModelSerializer):
    account_name = serializers.SerializerMethodField()
    warehouse_name = serializers.SerializerMethodField()
    comptages = serializers.SerializerMethodField()

    class Meta:
        model = Inventory
        fields = [
            'id', 'label', 'date', 'status', 'end_status_date',
            'lunch_status_date', 'current_status_date', 'pending_status_date',
            'account_name', 'warehouse_name', 'comptages'
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