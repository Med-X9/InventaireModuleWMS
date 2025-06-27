from rest_framework import serializers
from ..models import Job, JobDetail, Location
from apps.masterdata.serializers.location_serializer import LocationSerializer
from apps.masterdata.serializers.sous_zone_serializer import SousZoneSerializer
from apps.masterdata.serializers.zone_serializer import ZoneSerializer

class JobCreateRequestSerializer(serializers.Serializer):
    emplacements = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )

class JobRemoveEmplacementsSerializer(serializers.Serializer):
    emplacement_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )

class JobAddEmplacementsSerializer(serializers.Serializer):
    emplacement_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )

class JobValidateRequestSerializer(serializers.Serializer):
    job_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )

class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ['id', 'reference', 'status', 'warehouse', 'inventory']

class JobDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobDetail
        fields = ['id', 'reference', 'location', 'job', 'status']

class EmplacementSerializer(serializers.Serializer):
    emplacements = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )

class PdaSerializer(serializers.Serializer):
    reference = serializers.CharField()
    session = serializers.IntegerField()

class InventoryJobUpdateSerializer(serializers.Serializer):
    date = serializers.DateField(required=False)
    jobs = serializers.ListField(child=EmplacementSerializer(), required=False)

class JobAssignmentRequestSerializer(serializers.Serializer):
    job_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )
    personne_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )

class InventoryJobRetrieveSerializer(serializers.Serializer):
    date = serializers.DateTimeField()
    warehouse_id = serializers.IntegerField()
    warehouse_name = serializers.CharField()
    inventory_id = serializers.IntegerField()
    inventory_label = serializers.CharField()
    jobs = JobSerializer(many=True)

class JobLocationDetailSerializer(serializers.ModelSerializer):
    sous_zone = SousZoneSerializer(source='location.sous_zone', read_only=True)
    zone = ZoneSerializer(source='location.sous_zone.zone', read_only=True)
    location_reference = serializers.CharField(source='location.location_reference', read_only=True)
    location_id = serializers.IntegerField(source='location.id', read_only=True)

    class Meta:
        model = JobDetail
        fields = ['id', 'location_id', 'reference', 'location_reference', 'sous_zone', 'zone', 'status']

class JobListWithLocationsSerializer(serializers.ModelSerializer):
    locations = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = ['id', 'reference', 'status', 'created_at', 'locations']

    def get_locations(self, obj):
        # Récupérer les paramètres de filtrage depuis la requête
        request = self.context.get('request')
        if not request:
            # Si pas de requête, retourner tous les emplacements
            job_details = obj.jobdetail_set.select_related('location__sous_zone__zone').all()
            return JobLocationDetailSerializer(job_details, many=True).data
        
        # Filtrer les emplacements selon les paramètres
        job_details = obj.jobdetail_set.select_related('location__sous_zone__zone').all()
        
        # Filtre par location_reference
        location_reference = request.query_params.get('location_reference')
        if location_reference:
            job_details = job_details.filter(location__location_reference__icontains=location_reference)
        
        # Filtre par sous_zone
        sous_zone = request.query_params.get('sous_zone')
        if sous_zone:
            job_details = job_details.filter(location__sous_zone_id=sous_zone)
        
        # Filtre par zone
        zone = request.query_params.get('zone')
        if zone:
            job_details = job_details.filter(location__sous_zone__zone_id=zone)
        
        return JobLocationDetailSerializer(job_details, many=True).data 