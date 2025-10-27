from rest_framework import serializers
from ..models import Job, JobDetail, Location, Assigment, JobDetailRessource, CountingDetail, Counting
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
        """
        Récupère les emplacements du job
        ⚠️ Règle: Le serializer ne doit PAS utiliser .all(), .filter() ou toute méthode ORM
        Les données doivent être préchargées via prefetch_related dans la vue
        """
        # Accéder directement aux job_details (déjà chargés via prefetch_related dans la vue)
        return JobLocationDetailSerializer(obj.jobdetail_set, many=True).data 

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
        help_text="Liste des IDs des jobs à marquer comme PRET"
    )

class JobAssignmentDetailSerializer(serializers.ModelSerializer):
    counting_order = serializers.IntegerField(source='counting.order', read_only=True)
    status = serializers.CharField()
    session = serializers.SerializerMethodField()
    date_start = serializers.DateTimeField(read_only=True)
    class Meta:
        model = Assigment
        fields = ['counting_order', 'status', 'session', 'date_start']
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

class PendingJobReferenceSerializer(serializers.Serializer):
    """
    Serializer pour les jobs en attente avec détails pour filtrage et pagination
    """
    id = serializers.IntegerField()
    reference = serializers.CharField()
    status = serializers.CharField()
    created_at = serializers.DateTimeField()
    inventory_id = serializers.IntegerField(source='inventory.id')
    inventory_reference = serializers.CharField(source='inventory.reference')
    inventory_label = serializers.CharField(source='inventory.label')
    warehouse_id = serializers.IntegerField(source='warehouse.id')
    warehouse_reference = serializers.CharField(source='warehouse.reference')
    warehouse_name = serializers.CharField(source='warehouse.warehouse_name')
    emplacements_count = serializers.SerializerMethodField()
    assignments_count = serializers.SerializerMethodField()

    def get_emplacements_count(self, obj):
        return obj.jobdetail_set.count()

    def get_assignments_count(self, obj):
        return obj.assigment_set.count()

class JobResetAssignmentsRequestSerializer(serializers.Serializer):
    job_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        help_text="Liste des IDs des jobs en attente à remettre en attente"
    ) 

class JobTransferRequestSerializer(serializers.Serializer):
    """
    Serializer pour transférer les jobs par comptage
    """
    job_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        help_text="Liste des IDs des jobs à transférer"
    )
    counting_order = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
        help_text="Liste des ordres de comptage pour lesquels transférer les jobs (ex: [1, 2, 3])"
    ) 

class JobProgressByCountingSerializer(serializers.Serializer):
    """
    Sérialiseur pour l'avancement des emplacements par job et par counting
    """
    job_id = serializers.IntegerField()
    job_reference = serializers.CharField()
    job_status = serializers.CharField()
    counting_order = serializers.IntegerField()
    counting_reference = serializers.CharField()
    counting_count_mode = serializers.CharField()
    total_emplacements = serializers.IntegerField()
    completed_emplacements = serializers.IntegerField()
    progress_percentage = serializers.FloatField()
    emplacements_details = serializers.ListField(child=serializers.DictField())

class EmplacementProgressSerializer(serializers.Serializer):
    """
    Sérialiseur pour les détails de progression d'un emplacement
    """
    location_id = serializers.IntegerField()
    location_reference = serializers.CharField()
    sous_zone_name = serializers.CharField()
    zone_name = serializers.CharField()
    status = serializers.CharField()
    counting_details = serializers.ListField(child=serializers.DictField()) 