from rest_framework import serializers
from django.utils import timezone
from datetime import datetime

class JobBatchAssignmentSerializer(serializers.Serializer):
    """
    Serializer pour l'affectation en lot de sessions et ressources aux jobs (nouveau format)
    """
    job_id = serializers.IntegerField(help_text="ID du job")
    team1 = serializers.IntegerField(required=False, allow_null=True, help_text="ID de la session du 1er comptage (optionnel)")
    date1 = serializers.DateTimeField(required=False, allow_null=True, help_text="Date d'affectation du 1er comptage (optionnel)")
    team2 = serializers.IntegerField(required=False, allow_null=True, help_text="ID de la session du 2ème comptage (optionnel)")
    date2 = serializers.DateTimeField(required=False, allow_null=True, help_text="Date d'affectation du 2ème comptage (optionnel)")
    resources = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list,
        help_text="Liste des IDs de ressources à affecter au job (optionnel)"
    )

    def validate_team1(self, value):
        """Valider team1"""
        if value is not None and (not isinstance(value, int) or value <= 0):
            raise serializers.ValidationError("team1 doit être un ID valide (nombre positif)")
        return value

    def validate_team2(self, value):
        """Valider team2"""
        if value is not None and (not isinstance(value, int) or value <= 0):
            raise serializers.ValidationError("team2 doit être un ID valide (nombre positif)")
        return value

    def validate_job_id(self, value):
        """Valider job_id"""
        if not isinstance(value, int) or value <= 0:
            raise serializers.ValidationError("job_id doit être un ID valide (nombre positif)")
        return value

    def validate_resources(self, value):
        """Valider la liste des ressources"""
        if value:
            for resource_id in value:
                if not isinstance(resource_id, int) or resource_id <= 0:
                    raise serializers.ValidationError(f"Ressource ID {resource_id} doit être un nombre positif")
        return value

class JobBatchAssignmentRequestSerializer(serializers.Serializer):
    """
    Serializer pour la requête d'affectation en lot (format direct)
    """
    def to_internal_value(self, data):
        """
        Accepte directement une liste de jobs ou une liste dans 'assignments'
        """
        try:
            if isinstance(data, list):
                # Format direct : [job1, job2, ...]
                return {'assignments': data}
            elif isinstance(data, dict) and 'assignments' in data:
                # Format avec clé assignments : {"assignments": [job1, job2, ...]}
                return data
            else:
                raise serializers.ValidationError("Format invalide. Attendu: liste de jobs ou {'assignments': [...]}")
        except Exception as e:
            raise serializers.ValidationError(f"Erreur de format: {str(e)}")

    assignments = serializers.ListField(
        child=JobBatchAssignmentSerializer(),
        min_length=1,
        help_text="Liste des jobs avec leurs affectations"
    )

    def validate_assignments(self, value):
        if not value:
            raise serializers.ValidationError("La liste des assignments ne peut pas être vide")
        
        try:
            job_ids = [job['job_id'] for job in value]
            if len(job_ids) != len(set(job_ids)):
                raise serializers.ValidationError("Les IDs des jobs doivent être uniques")
        except (KeyError, TypeError) as e:
            raise serializers.ValidationError(f"Format invalide dans assignments: {str(e)}")
        
        return value

    def validate(self, data):
        try:
            for job_data in data['assignments']:
                job_id = job_data.get('job_id')
                if not job_id:
                    raise serializers.ValidationError("job_id est obligatoire pour chaque job")
                
                has_team1 = job_data.get('team1') is not None
                has_team2 = job_data.get('team2') is not None
                has_resources = job_data.get('resources', [])
                
                if not (has_team1 or has_team2 or has_resources):
                    raise serializers.ValidationError(
                        f"Le job {job_id} doit avoir au moins une affectation (team1, team2 ou resources)"
                    )
                
                # Si team1 fourni sans date1, date1 = now
                if has_team1 and job_data.get('date1') is None:
                    job_data['date1'] = timezone.now()
                # Si team2 fourni sans date2, date2 = now
                if has_team2 and job_data.get('date2') is None:
                    job_data['date2'] = timezone.now()
        except Exception as e:
            raise serializers.ValidationError(f"Erreur de validation: {str(e)}")
        
        return data

class JobBatchAssignmentResponseSerializer(serializers.Serializer):
    """
    Serializer pour la réponse d'affectation en lot
    """
    success = serializers.BooleanField()
    message = serializers.CharField()
    total_jobs_processed = serializers.IntegerField()
    jobs_results = serializers.ListField()
    processing_date = serializers.DateTimeField()

class JobAssignmentResultSerializer(serializers.Serializer):
    """
    Serializer pour le résultat d'affectation d'un job
    """
    job_id = serializers.IntegerField()
    job_reference = serializers.CharField()
    assignments_created = serializers.IntegerField()
    assignments_updated = serializers.IntegerField()
    resources_created = serializers.IntegerField()
    resources_updated = serializers.IntegerField()
    errors = serializers.ListField(
        child=serializers.CharField(),
        default=list
    ) 