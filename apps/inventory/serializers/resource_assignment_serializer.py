from rest_framework import serializers
from ..models import JobDetailRessource
from apps.masterdata.models import Ressource

class ResourceAssignmentSerializer(serializers.Serializer):
    """Serializer pour l'affectation de ressources à un job"""
    
    resource_id = serializers.IntegerField(
        help_text="ID de la ressource à affecter"
    )
    quantity = serializers.IntegerField(
        default=1,
        min_value=1,
        help_text="Quantité de la ressource à affecter (défaut: 1)"
    )

class JobResourceAssignmentSerializer(serializers.Serializer):
    """Serializer pour l'affectation de ressources à un job spécifique"""
    
    job_id = serializers.IntegerField(
        help_text="ID du job"
    )
    resource_assignments = ResourceAssignmentSerializer(
        many=True,
        help_text="Liste des ressources à affecter avec leurs quantités"
    )

class AssignResourcesToJobsSerializer(serializers.Serializer):
    """Serializer pour l'affectation de ressources communes à plusieurs jobs"""
    
    job_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="Liste des IDs des jobs"
    )
    resource_assignments = serializers.ListField(
        child=ResourceAssignmentSerializer(),
        help_text="Liste des ressources à affecter à tous les jobs"
    )

class JobResourceDetailSerializer(serializers.ModelSerializer):
    """Serializer pour les détails d'une ressource affectée à un job"""
    
    resource_id = serializers.IntegerField(source='ressource.id', read_only=True)
    resource_name = serializers.CharField(source='ressource.libelle', read_only=True)
    resource_code = serializers.CharField(source='ressource.reference', read_only=True)
    
    class Meta:
        model = JobDetailRessource
        fields = [
            'id', 'reference', 'resource_id', 'resource_name', 
            'resource_code', 'quantity', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'reference', 'created_at', 'updated_at']

class RemoveResourcesFromJobSerializer(serializers.Serializer):
    """Serializer pour la suppression de ressources d'un job"""
    
    resource_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="Liste des IDs des ressources à supprimer du job"
    )

class ResourceAssignmentResponseSerializer(serializers.Serializer):
    """Serializer pour la réponse d'affectation de ressources"""
    
    success = serializers.BooleanField()
    message = serializers.CharField()
    assignments_created = serializers.IntegerField()
    assignments_updated = serializers.IntegerField()
    total_assignments = serializers.IntegerField()
    job_id = serializers.IntegerField()
    job_reference = serializers.CharField()

class BatchResourceAssignmentResponseSerializer(serializers.Serializer):
    """Serializer pour la réponse d'affectation de ressources en lot"""
    
    success = serializers.BooleanField()
    message = serializers.CharField()
    total_jobs_processed = serializers.IntegerField()
    total_assignments_created = serializers.IntegerField()
    total_assignments_updated = serializers.IntegerField()
    job_results = serializers.ListField(
        child=ResourceAssignmentResponseSerializer(),
        help_text="Résultats détaillés par job"
    )

class ResourceRemovalResponseSerializer(serializers.Serializer):
    """Serializer pour la réponse de suppression de ressources"""
    
    success = serializers.BooleanField()
    message = serializers.CharField()
    deleted_count = serializers.IntegerField()
    job_id = serializers.IntegerField()
    job_reference = serializers.CharField() 