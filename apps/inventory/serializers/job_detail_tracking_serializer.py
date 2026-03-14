"""
Sérialiseurs pour le suivi des JobDetail avec Assignment.
"""
from rest_framework import serializers
from ..models import JobDetail, Assigment


class JobDetailTrackingSerializer(serializers.Serializer):
    """
    Serializer pour un JobDetail avec son Assignment correspondant.
    """
    
    # Informations du JobDetail
    id = serializers.IntegerField(source='job_detail.id')
    reference = serializers.CharField(source='job_detail.reference')
    location_reference = serializers.CharField(source='job_detail.location.location_reference', read_only=True)
    location_id = serializers.IntegerField(source='job_detail.location.id', read_only=True)
    status = serializers.CharField(source='job_detail.status')
    en_attente_date = serializers.DateTimeField(source='job_detail.en_attente_date', allow_null=True)
    termine_date = serializers.DateTimeField(source='job_detail.termine_date', allow_null=True)
    
    # Informations du Job
    job_reference = serializers.CharField(source='job_detail.job.reference', read_only=True)
    job_id = serializers.IntegerField(source='job_detail.job.id', read_only=True)
    
    # Informations de l'Assignment (peut être None)
    assignment_id = serializers.IntegerField(source='assignment.id', allow_null=True, read_only=True)
    assignment_reference = serializers.CharField(source='assignment.reference', allow_null=True, read_only=True)
    assignment_status = serializers.CharField(source='assignment.status', allow_null=True, read_only=True)
    transfert_date = serializers.DateTimeField(source='assignment.transfert_date', allow_null=True, read_only=True)
    entame_date = serializers.DateTimeField(source='assignment.entame_date', allow_null=True, read_only=True)
    termine_date_assignment = serializers.SerializerMethodField()
    
    def get_termine_date_assignment(self, obj):
        """
        Retourne la date de fin de l'assignment.
        Si le statut est TERMINE, on peut utiliser updated_at ou une date spécifique.
        """
        # obj est un dictionnaire avec 'job_detail' et 'assignment'
        assignment = obj.get('assignment') if isinstance(obj, dict) else None
        if assignment and assignment.status == 'TERMINE':
            # Si pas de champ termine_date dans Assignment, utiliser updated_at
            return assignment.updated_at if hasattr(assignment, 'updated_at') else None
        return None

