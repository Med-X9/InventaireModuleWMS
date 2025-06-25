from rest_framework import serializers
from ..models import Warehouse, Inventory, Location, Job, Assigment, JobDetail
from django.utils import timezone
from .job_serializer import EmplacementSerializer, PdaSerializer

class InventoryJobCreateSerializer(serializers.Serializer):
    date = serializers.DateField()
    warehouse = serializers.PrimaryKeyRelatedField(queryset=Warehouse.objects.all())
    inventory = serializers.PrimaryKeyRelatedField(queryset=Inventory.objects.all())
    jobs = serializers.ListField(child=EmplacementSerializer())
    pda = serializers.ListField(child=PdaSerializer())

    def validate_jobs(self, value):
        for job in value:
            for emplacement_id in job['emplacements']:
                try:
                    Location.objects.get(id=emplacement_id)
                except Location.DoesNotExist:
                    raise serializers.ValidationError(f"Emplacement {emplacement_id} n'existe pas")
        return value

# Serializers pour la récupération des données
class JobDetailRetrieveSerializer(serializers.ModelSerializer):
    location_id = serializers.IntegerField(source='location.id')
    location_name = serializers.CharField(source='location.location_code')
    pda_name = serializers.CharField(source='pda.reference')
    pda_session = serializers.IntegerField(source='pda.session.id')

    class Meta:
        model = JobDetail
        fields = ['id', 'location_id', 'location_name', 'pda_name', 'pda_session', 'status']

class JobRetrieveSerializer(serializers.ModelSerializer):
    details = JobDetailRetrieveSerializer(source='jobdetail_set', many=True, read_only=True)

    class Meta:
        model = Job
        fields = ['id', 'reference', 'status', 'details']

class InventoryJobRetrieveSerializer(serializers.Serializer):
    date = serializers.DateTimeField()
    warehouse_id = serializers.IntegerField()
    warehouse_name = serializers.CharField()
    inventory_id = serializers.IntegerField()
    inventory_label = serializers.CharField()
    jobs = JobRetrieveSerializer(many=True)
    pda = PdaSerializer(many=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Convertir le datetime en date
        if data['date']:
            data['date'] = data['date'].date()
        return data 