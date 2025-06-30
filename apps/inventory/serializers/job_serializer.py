from rest_framework import serializers
from ..models import Job, JobDetail, Location, Assigment, JobDetailRessource
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

class JobDeleteRequestSerializer(serializers.Serializer):
    job_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        help_text="Liste des IDs des jobs à supprimer"
    )

class JobReadyRequestSerializer(serializers.Serializer):
    job_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        help_text="Liste des IDs des jobs à traiter"
    )
    orders = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        help_text="Liste des ordres de comptage à marquer comme PRET pour ces jobs"
    )

class JobAssignmentDetailSerializer(serializers.ModelSerializer):
    counting_order = serializers.IntegerField(source='counting.order', read_only=True)
    status = serializers.CharField()
    session = serializers.SerializerMethodField()
    class Meta:
        model = Assigment
        fields = ['counting_order', 'status', 'session']
    def get_session(self, obj):
        if obj.session:
            return {'id': obj.session.id, 'username': obj.session.username}
        return None

class JobRessourceSerializer(serializers.ModelSerializer):
    reference = serializers.CharField(source='ressource.reference')
    class Meta:
        model = JobDetailRessource
        fields = ['id', 'reference', 'quantity']

class JobEmplacementDetailSerializer(serializers.ModelSerializer):
    sous_zone = SousZoneSerializer(source='location.sous_zone', read_only=True)
    zone = ZoneSerializer(source='location.sous_zone.zone', read_only=True)
    reference = serializers.CharField(source='location.location_reference', read_only=True)
    class Meta:
        model = JobDetail
        fields = ['id', 'reference', 'sous_zone', 'zone']

class JobFullDetailSerializer(serializers.ModelSerializer):
    emplacements = serializers.SerializerMethodField()
    assignments = serializers.SerializerMethodField()
    ressources = serializers.SerializerMethodField()
    class Meta:
        model = Job
        fields = ['id', 'reference', 'status', 'emplacements', 'assignments', 'ressources']
    def get_emplacements(self, obj):
        job_details = obj.jobdetail_set.select_related('location__sous_zone__zone').all()
        return JobEmplacementDetailSerializer(job_details, many=True).data
    def get_assignments(self, obj):
        assignments = obj.assigment_set.select_related('counting', 'session').all()
        return JobAssignmentDetailSerializer(assignments, many=True).data
    def get_ressources(self, obj):
        ressources = obj.jobdetailressource_set.select_related('ressource').all()
        return JobRessourceSerializer(ressources, many=True).data 

class JobPendingSerializer(serializers.ModelSerializer):
    emplacements = serializers.SerializerMethodField()
    assignments = serializers.SerializerMethodField()
    ressources = serializers.SerializerMethodField()
    
    class Meta:
        model = Job
        fields = ['id', 'reference', 'status', 'emplacements', 'assignments', 'ressources']
    
    def get_emplacements(self, obj):
        job_details = obj.jobdetail_set.select_related('location__sous_zone__zone').all()
        return JobEmplacementDetailSerializer(job_details, many=True).data
    
    def get_assignments(self, obj):
        assignments = obj.assigment_set.select_related('counting', 'session').all()
        return JobAssignmentDetailSerializer(assignments, many=True).data
    
    def get_ressources(self, obj):
        ressources = obj.jobdetailressource_set.select_related('ressource').all()
        return JobRessourceSerializer(ressources, many=True).data 

class JobResetAssignmentsRequestSerializer(serializers.Serializer):
    job_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        help_text="Liste des IDs des jobs en attente à remettre en attente"
    ) 