from rest_framework import serializers
from ..models import Counting, Job, JobDetail, Inventory, Location
from apps.masterdata.serializers.location_serializer import LocationSerializer as MasterDataLocationSerializer
from apps.masterdata.serializers.sous_zone_serializer import SousZoneSerializer
from apps.masterdata.serializers.zone_serializer import ZoneSerializer


class LocationSerializer(serializers.ModelSerializer):
    """Serializer simple pour les emplacements"""
    zone = ZoneSerializer(source='sous_zone.zone', read_only=True)
    sous_zone = SousZoneSerializer(read_only=True)
    
    class Meta:
        model = Location
        fields = ['id', 'reference', 'zone', 'sous_zone']


class JobDetailSerializer(serializers.ModelSerializer):
    """Serializer pour les détails des jobs (emplacements)"""
    location = LocationSerializer(read_only=True)
    
    class Meta:
        model = JobDetail
        fields = ['id', 'reference', 'location', 'status', 'en_attente_date', 'termine_date']


class JobSerializer(serializers.ModelSerializer):
    """Serializer pour les jobs avec leurs emplacements"""
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    job_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Job
        fields = [
            'id', 'reference', 'status', 'warehouse_name',
            'en_attente_date', 'affecte_date', 'pret_date', 'transfert_date',
            'entame_date', 'valide_date', 'termine_date', 'saisie_manuelle_date',
            'job_details'
        ]
    
    def get_job_details(self, obj):
        """Récupère les job_details pour ce job et le comptage spécifique"""
        counting = self.context.get('counting')
        if counting:
            # Filtrer les job_details par comptage
            job_details = obj.jobdetail_set.filter(counting=counting)
        else:
            # Si pas de comptage spécifique, retourner tous les job_details
            job_details = obj.jobdetail_set.all()
        
        return JobDetailSerializer(job_details, many=True).data


class CountingSerializer(serializers.ModelSerializer):
    """Serializer pour un comptage avec ses jobs et emplacements"""
    jobs = serializers.SerializerMethodField()
    
    class Meta:
        model = Counting
        fields = [
            'id', 'reference', 'order', 'count_mode', 'unit_scanned', 'entry_quantity',
            'is_variant', 'n_lot', 'n_serie', 'dlc', 'show_product', 'stock_situation',
            'quantity_show', 'jobs'
        ]
    
    def get_jobs(self, obj):
        """Récupère les jobs associés à ce comptage via JobDetail"""
        # Récupérer les jobs qui ont des JobDetail liés à ce comptage
        job_ids = obj.jobdetail_set.values_list('job_id', flat=True).distinct()
        jobs = Job.objects.filter(id__in=job_ids).prefetch_related(
            'warehouse',
            'jobdetail_set__location__sous_zone__zone',
            'jobdetail_set__location__sous_zone'
        )
        # Passer le contexte du comptage pour filtrer les job_details
        context = {'counting': obj}
        return JobSerializer(jobs, many=True, context=context).data


class InventoryCountingTrackingSerializer(serializers.ModelSerializer):
    """Serializer principal pour le suivi d'un inventaire regroupé par comptages"""
    countings = CountingSerializer(many=True, read_only=True)
    
    class Meta:
        model = Inventory
        fields = [
            'id', 'reference', 'label', 'date', 'status', 'inventory_type',
            'en_preparation_status_date', 'en_realisation_status_date',
            'termine_status_date', 'cloture_status_date', 'countings'
        ]